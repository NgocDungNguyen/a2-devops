"""
Order pricing and lifecycle.

Everything monetary is computed here, on the server, from the product rows.
The application this replaces took the order total from the request body and
stored it without checking — a shopper could set their own price.

Tax reproduces server/config/tax.js: a flat rate applied only to products
flagged taxable.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from apps.catalog.models import Product
from apps.orders import payments
from apps.orders.models import (
    Order,
    OrderItem,
    OrderItemStatus,
    OrderStatus,
    PaymentStatus,
)

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value):
    """Round to cents, half up — the way a till does it."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def tax_for(amount, taxable):
    """Sales tax on a line total."""
    if not taxable:
        return ZERO
    return money(Decimal(amount) * Decimal(str(settings.SALES_TAX_RATE)))


@transaction.atomic
def create_order(user, items, payment, request=None):
    """Place an order.

    `items` is a list of {"product": <id>, "quantity": <int>}. Prices, tax and
    the total all come from the database, never from the caller. `payment` is
    the validated card from PaymentSerializer.

    The whole thing runs in one transaction with the product rows locked, so
    two shoppers racing for the last unit cannot both succeed — the original
    issued an unordered bulkWrite of increments with no stock check at all and
    could drive quantity negative.

    Order of operations matters. Stock is checked, then the card is
    authorised, and only then is anything written. A decline raises out of the
    transaction, so a shopper whose card fails leaves behind no order row and
    no decremented stock - the alternative, taking the stock first and putting
    it back on failure, is the bug that lets a stream of failed checkouts
    empty a shelf.
    """
    if not items:
        raise serializers.ValidationError({"items": "Your bag is empty."})

    # Collapse duplicate lines for the same product into one.
    wanted = {}
    for entry in items:
        product_id = entry["product"].pk if hasattr(entry["product"], "pk") else entry["product"]
        wanted[product_id] = wanted.get(product_id, 0) + int(entry["quantity"])

    # `of=("self",)` locks only the product rows. Without it Postgres refuses
    # the query outright — brand is nullable, so select_related() emits a LEFT
    # OUTER JOIN, and FOR UPDATE cannot be applied to the nullable side of one.
    locked = {
        p.pk: p
        for p in Product.objects.select_for_update(of=("self",))
        .select_related("brand")
        .filter(pk__in=wanted.keys())
    }

    order_items = []
    subtotal = ZERO
    total_tax = ZERO

    for product_id, quantity in wanted.items():
        product = locked.get(product_id)
        if product is None:
            raise serializers.ValidationError(
                {"items": f"Product {product_id} no longer exists."}
            )
        if not product.is_active:
            raise serializers.ValidationError(
                {"items": f"'{product.name}' is no longer available."}
            )
        if quantity < 1:
            raise serializers.ValidationError(
                {"items": f"Quantity for '{product.name}' must be at least 1."}
            )
        if product.quantity < quantity:
            raise serializers.ValidationError(
                {
                    "items": (
                        f"Only {product.quantity} of '{product.name}' "
                        f"remain in stock."
                    )
                }
            )

        unit = money(product.price)
        line_total = money(unit * quantity)
        line_tax = tax_for(line_total, product.taxable)

        subtotal += line_total
        total_tax += line_tax

        order_items.append(
            OrderItem(
                product=product,
                # Snapshots, so this order still reads correctly after the
                # product is renamed, repriced or removed from the catalogue.
                product_name=product.name,
                product_slug=product.slug,
                # The storage key, not a URL — see the field's comment.
                product_image_key=product.image.name if product.image else "",
                brand_name=product.brand.name if product.brand else "",
                quantity=quantity,
                purchase_price=unit,
                total_price=line_total,
                total_tax=line_tax,
                price_with_tax=line_total + line_tax,
                taxable=product.taxable,
            )
        )

    total = subtotal + total_tax

    # The card is charged here, after the basket is known to be servable and
    # before a single row is written. PaymentDeclined propagates out of the
    # atomic block, so everything above is rolled back.
    charge = payments.authorise(
        number=payment["number"],
        exp_month=payment["exp_month"],
        exp_year=payment["exp_year"],
        cvc=payment["cvc"],
        amount=total,
    )

    order = Order.objects.create(
        user=user,
        subtotal=subtotal,
        total_tax=total_tax,
        total=total,
        payment_status=PaymentStatus.PAID,
        payment_reference=charge.reference,
        card_brand=charge.brand,
        card_last4=charge.last4,
    )
    for item in order_items:
        item.order = order
    OrderItem.objects.bulk_create(order_items)

    # F() keeps the decrement in the database, so it is correct even if
    # another transaction touched the row between the read and the write.
    for product_id, quantity in wanted.items():
        Product.objects.filter(pk=product_id).update(
            quantity=F("quantity") - quantity
        )

    return order


@transaction.atomic
def set_item_status(order, item, new_status):
    """Move one line item along the fulfilment path.

    Cancelling restores the stock and re-sums the order. When every line has
    been cancelled the order is marked cancelled rather than deleted — the
    original removed the order and its cart outright, which erased the
    customer's purchase history and made their own bookmarked order link 404.

    Cancelling is a one-way door. Reviving a cancelled line would have to take
    the stock back off the shelf (which may no longer be there) and re-charge a
    card that has already been refunded, and doing neither — which is what
    happens if you simply allow the status to change — leaves an order that is
    "placed" but "refunded", with stock that was given back and never retaken.
    Re-order instead; that is a checkout, and checkout is where stock and
    payment are handled properly.
    """
    previous = item.status
    if previous == new_status:
        return order

    if previous == OrderItemStatus.CANCELLED:
        raise serializers.ValidationError(
            {
                "status": (
                    "This item was cancelled and its stock returned. "
                    "Place a new order for it instead."
                )
            }
        )

    item.status = new_status
    item.save(update_fields=["status", "updated_at"])

    # The guard above guarantees `previous` was not already cancelled, so this
    # can never hand the same units back twice.
    if new_status == OrderItemStatus.CANCELLED:
        Product.objects.filter(pk=item.product_id).update(
            quantity=F("quantity") + item.quantity
        )

    order.recalculate_totals()

    statuses = set(order.items.values_list("status", flat=True))
    if statuses == {OrderItemStatus.CANCELLED}:
        order.status = OrderStatus.CANCELLED
        # Nothing is left to ship, so the money goes back. An order sitting at
        # "cancelled" while still marked "paid" is the kind of inconsistency
        # that turns into a support ticket.
        order.payment_status = PaymentStatus.REFUNDED
    else:
        # Still something to fulfil, so the order is live and stays paid. A
        # partial cancellation lowers the total without refunding the
        # difference — see the note in the README; partial refunds need a real
        # gateway.
        order.status = OrderStatus.PLACED
    order.save(update_fields=["status", "payment_status", "updated_at"])

    return order


@transaction.atomic
def cancel_order(order):
    """Cancel every line that is not already cancelled, and restock."""
    for item in order.items.exclude(status=OrderItemStatus.CANCELLED):
        Product.objects.filter(pk=item.product_id).update(
            quantity=F("quantity") + item.quantity
        )
        item.status = OrderItemStatus.CANCELLED
        item.save(update_fields=["status", "updated_at"])

    order.status = OrderStatus.CANCELLED
    order.payment_status = PaymentStatus.REFUNDED
    order.recalculate_totals()
    order.save(update_fields=["status", "payment_status", "updated_at"])
    return order
