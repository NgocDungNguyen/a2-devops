"""Merchant serializers."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.merchants.models import Merchant, MerchantStatus
from apps.merchants.services import read_invite_token

User = get_user_model()


class MerchantApplicationSerializer(serializers.ModelSerializer):
    """The public "become a seller" form."""

    business = serializers.CharField(min_length=10)

    class Meta:
        model = Merchant
        fields = ["id", "name", "email", "phone_number", "brand_name", "business"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = value.lower().strip()
        if Merchant.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "We have already received an application from this email address."
            )
        return value

    def create(self, validated_data):
        return Merchant.objects.create(
            status=MerchantStatus.WAITING, is_active=False, **validated_data
        )


class MerchantSerializer(serializers.ModelSerializer):
    """The admin merchant list."""

    brand_name_actual = serializers.CharField(
        source="brand.name", read_only=True, default=None
    )
    brand_is_active = serializers.BooleanField(
        source="brand.is_active", read_only=True, default=None
    )
    has_account = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = [
            "id",
            "name",
            "email",
            "phone_number",
            "brand_name",
            "brand_name_actual",
            "brand_is_active",
            "business",
            "status",
            "is_active",
            "has_account",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            f for f in fields if f != "is_active"
        ]  # only is_active is writable, via PATCH

    def get_has_account(self, obj) -> bool:
        return User.objects.filter(email__iexact=obj.email).exists()


class MerchantSignupSerializer(serializers.Serializer):
    """Accepting an invitation."""

    token = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(min_length=8, style={"input_type": "password"})
    confirm_password = serializers.CharField(style={"input_type": "password"})

    INVALID = "This invitation link is invalid or has expired."

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The two passwords do not match."}
            )

        merchant_id = read_invite_token(attrs["token"])
        if merchant_id is None:
            raise serializers.ValidationError({"detail": self.INVALID})

        merchant = Merchant.objects.filter(
            pk=merchant_id, status=MerchantStatus.APPROVED
        ).first()
        if merchant is None:
            raise serializers.ValidationError({"detail": self.INVALID})

        # Single use: once a password is set, the same link stops working.
        user = User.objects.filter(email__iexact=merchant.email).first()
        if user is not None and user.has_usable_password():
            raise serializers.ValidationError(
                {"detail": "This invitation has already been used. Please sign in."}
            )

        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        attrs["merchant"] = merchant
        return attrs
