"""
Orders and order line items.

There is deliberately no Cart model here. In the application this replaces,
the shopping cart lived in the browser's localStorage; the server-side "Cart"
document was created at checkout purely as a container for the order's line
items, and the Order was a thin wrapper holding only a total. Three of its
four cart endpoints were never called by the frontend. Line items belong on
the order, so that is where they are.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum

from apps.core.models import TimeStampedModel

_ZERO = Decimal("0.00")


class OrderStatus(models.TextChoices):
    PLACED = "placed", "Placed"
    CANCELLED = "cancelled", "Cancelled"


class PaymentStatus(models.TextChoices):
    """There is no "pending" here on purpose.

    The card is authorised before the order row is written, inside the same
    transaction - so an order that exists is an order that was paid for. A
    pending state would only be meaningful with an asynchronous gateway that
    confirms by webhook, which is a Plan F exercise rather than something to
    pretend at now.
    """

    PAID = "paid", "Paid"
    REFUNDED = "refunded", "Refunded"


class OrderItemStatus(models.TextChoices):
    """Per-line fulfilment status — the same five values as the original."""

    NOT_PROCESSED = "not_processed", "Not processed"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


class Order(TimeStampedModel):
    """A placed order. The primary key doubles as the order number."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        db_index=True,
    )
    status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PLACED
    )

    # All three are computed on the server from the products themselves. The
    # MERN app accepted the total from the client and never checked it.
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # --- payment -----------------------------------------------------------
    # What is stored is what a real integration is allowed to store: the
    # gateway's reference, the brand, and the last four digits. The card
    # number, the expiry and the security code are used to authorise the
    # charge and then discarded with the request. Never add a column for them.
    payment_status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PAID
    )
    payment_reference = models.CharField(max_length=64, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk}"

    def recalculate_totals(self, save=True):
        """Re-sum the order from its surviving (non-cancelled) line items.

        Deliberately aggregated in the database rather than in Python over
        `self.items.all()`: the view prefetches the items, and iterating that
        cached list would re-read the statuses as they were before the update
        that triggered this call.
        """
        totals = self.items.exclude(status=OrderItemStatus.CANCELLED).aggregate(
            subtotal=Sum("total_price"), tax=Sum("total_tax")
        )
        self.subtotal = totals["subtotal"] or _ZERO
        self.total_tax = totals["tax"] or _ZERO
        self.total = self.subtotal + self.total_tax
        if save:
            self.save(update_fields=["subtotal", "total_tax", "total", "updated_at"])
        return self


class OrderItem(TimeStampedModel):
    """One product on an order.

    The product name, slug, image and brand are snapshotted at purchase time,
    and the product itself is PROTECTed from deletion. In the original, order
    history was rendered by following a reference to the live product, so
    deleting a product retroactively corrupted every order that contained it.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="order_items"
    )

    product_name = models.CharField(max_length=200)
    product_slug = models.CharField(max_length=220, blank=True)
    # The storage key, e.g. "products/8bac1aca.jpg" — deliberately not a full
    # URL. Storing a URL would bake this host and port into the row, so every
    # historical order's thumbnail would break the day the API moves to a
    # different instance or gets a load balancer in front of it. The URL is
    # built at serialization time instead.
    product_image_key = models.CharField(max_length=255, blank=True)
    brand_name = models.CharField(max_length=120, blank=True)

    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_with_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxable = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=OrderItemStatus.choices,
        default=OrderItemStatus.NOT_PROCESSED,
        db_index=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"
