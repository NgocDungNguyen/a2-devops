"""Order serializers."""

from rest_framework import serializers

from apps.catalog.models import Product
from apps.core.serializers import absolute_storage_url
from apps.orders import payments
from apps.orders.models import Order, OrderItem, OrderItemStatus


class OrderItemSerializer(serializers.ModelSerializer):
    # Resolved from the stored storage key on the way out, so a historical
    # order keeps working after the API moves host or media moves to S3.
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_slug",
            "product_image",
            "brand_name",
            "quantity",
            "purchase_price",
            "total_price",
            "total_tax",
            "price_with_tax",
            "taxable",
            "status",
        ]
        read_only_fields = fields

    def get_product_image(self, obj) -> str | None:
        return absolute_storage_url(self.context.get("request"), obj.product_image_key)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source="user.email", read_only=True)
    customer_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "subtotal",
            "total_tax",
            "total",
            "items",
            "item_count",
            "customer_email",
            "customer_name",
            "payment_status",
            "payment_reference",
            "card_brand",
            "card_last4",
            "created_at",
        ]
        read_only_fields = fields

    def get_item_count(self, obj) -> int:
        return sum(i.quantity for i in obj.items.all())


class OrderListSerializer(serializers.ModelSerializer):
    """The lighter shape used for order lists — no line items."""

    item_count = serializers.IntegerField(read_only=True, default=0)
    customer_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "subtotal",
            "total_tax",
            "total",
            "item_count",
            "customer_email",
            "payment_status",
            "card_brand",
            "card_last4",
            "created_at",
        ]
        read_only_fields = fields


class OrderCreateItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class PaymentSerializer(serializers.Serializer):
    """The card, on its way in and nowhere else.

    Every field is write_only, so none of this can ever be echoed back in a
    response by accident - which is exactly the sort of mistake that turns a
    checkout into an incident. What survives the request is the brand and the
    last four digits, written by the service layer.

    The validation here is the kind a payment form does locally: the Luhn
    check digit, a plausible expiry, the right length of security code. It
    catches typing mistakes. Whether the card actually pays is the gateway's
    decision, and that lives in payments.authorise().
    """

    number = serializers.CharField(write_only=True, max_length=32)
    exp_month = serializers.IntegerField(write_only=True, min_value=1, max_value=12)
    exp_year = serializers.IntegerField(write_only=True, min_value=2000, max_value=2100)
    cvc = serializers.CharField(write_only=True, max_length=4)
    name_on_card = serializers.CharField(
        write_only=True, max_length=120, required=False, allow_blank=True
    )

    def validate_number(self, value):
        if not payments.luhn_valid(value):
            raise serializers.ValidationError(
                "That card number is not valid. Check it and try again."
            )
        return payments.normalise(value)

    def validate_cvc(self, value):
        if not payments.normalise(value).isdigit():
            raise serializers.ValidationError("The security code must be digits.")
        return payments.normalise(value)

    def validate(self, attrs):
        # Length of the security code depends on the brand, so it can only be
        # checked once the number is known.
        expected = payments.cvc_length_for(attrs["number"])
        if len(attrs["cvc"]) != expected:
            raise serializers.ValidationError(
                {"cvc": f"The security code for this card must be {expected} digits."}
            )
        if payments.has_expired(attrs["exp_month"], attrs["exp_year"]):
            raise serializers.ValidationError(
                {"exp_year": "That expiry date is in the past."}
            )
        return attrs


class OrderCreateSerializer(serializers.Serializer):
    """Checkout.

    Note what is absent: no prices, no total. The client sends what it wants
    to buy, how many, and a card; the server decides what that costs and
    whether the card pays for it.
    """

    items = OrderCreateItemSerializer(many=True, allow_empty=False)
    payment = PaymentSerializer()


class OrderItemStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderItemStatus.choices)
