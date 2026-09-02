"""Django admin for orders.

This is the staff-facing back office at `/admin/`, and it is a different thing
from the REST API: it talks to the models directly, so none of the service
layer's rules apply here. That is exactly why so much is marked read-only
below — the admin is for *looking at* orders and for the occasional supported
correction, not for editing history.
"""

from django.contrib import admin

from apps.orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """The order's line items, shown on the order page rather than their own.

    Everything except the status is a purchase-time snapshot, so it is
    read-only: changing the price on a line here would silently rewrite what
    the customer was charged last month, and the totals on the order would no
    longer add up. Status stays editable so support can nudge a line along
    when the storefront cannot.
    """

    model = OrderItem
    extra = 0
    readonly_fields = [
        "product",
        "product_name",
        "quantity",
        "purchase_price",
        "total_price",
        "total_tax",
        "price_with_tax",
        "taxable",
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "status",
        "payment_status",
        "card_brand",
        "card_last4",
        "total",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "created_at"]
    search_fields = ["id", "user__email", "payment_reference"]
    autocomplete_fields = ["user"]
    # Totals are re-derived from the line items by Order.recalculate_totals(),
    # and the card details come back from the gateway at checkout. Neither is
    # something a human should be able to type over: an edited total would be
    # overwritten the next time a line changed, and an edited card reference
    # would no longer match anything the gateway can be asked about.
    #
    # `payment_status` is deliberately *not* here. Marking an order refunded by
    # hand is a real thing support does after refunding out-of-band, and this
    # is the only place to do it.
    readonly_fields = [
        "subtotal",
        "total_tax",
        "total",
        "payment_reference",
        "card_brand",
        "card_last4",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline]
