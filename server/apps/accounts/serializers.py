"""Serializers for authentication, profiles and addresses."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import Address, Role

User = get_user_model()


class MerchantSummarySerializer(serializers.Serializer):
    """The slice of a merchant record the SPA needs to render a seller's UI."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    brand_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    brand_id = serializers.IntegerField(read_only=True, allow_null=True)


class UserSerializer(serializers.ModelSerializer):
    """The authenticated user's own profile — GET /api/users/me/."""

    full_name = serializers.CharField(read_only=True)
    merchant = MerchantSummarySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "role",
            "provider",
            "avatar",
            "merchant",
            "created_at",
        ]
        read_only_fields = fields


class MeUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/users/me/ — deliberately only three writable fields.

    The application this replaces assigned the whole request body onto the
    user document, which let anyone promote themselves to administrator by
    including a role field. An explicit field list makes that impossible by
    construction rather than by remembering to blocklist the dangerous names.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number"]


class AdminUserSerializer(serializers.ModelSerializer):
    """The user list an administrator sees."""

    full_name = serializers.CharField(read_only=True)
    merchant_name = serializers.CharField(
        source="merchant.name", read_only=True, default=None
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "role",
            "provider",
            "is_active",
            "merchant_name",
            "created_at",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    is_subscribed = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "is_subscribed"]

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email address already exists."
            )
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data):
        validated_data.pop("is_subscribed", None)
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password, role=Role.MEMBER, **validated_data
        )


class LoginSerializer(TokenObtainPairSerializer):
    """Issues the access/refresh pair and embeds role + email as claims.

    The claims let the SPA's router pick a dashboard layout before
    /api/users/me/ has come back. They are a rendering hint only — every
    authorisation decision is made server-side against the database.
    """

    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        help_text="The refresh token to revoke. It is added to the blacklist."
    )


class PasswordForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    """Completes a reset started from the emailed link."""

    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, style={"input_type": "password"})
    confirm_password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The two passwords do not match."}
            )

        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {"detail": "This password reset link is invalid or has expired."}
            ) from None

        # The token embeds the current password hash and last_login, so it
        # invalidates itself once used — no columns to clear by hand, and no
        # window where a failed save leaves a live token behind.
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"detail": "This password reset link is invalid or has expired."}
            )

        try:
            validate_password(attrs["password"], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password", "updated_at"])
        return user

    @staticmethod
    def make_link(user, client_url):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return f"{client_url}/reset-password/{uid}/{token}"


class PasswordChangeSerializer(serializers.Serializer):
    """Changing your password while signed in."""

    current_password = serializers.CharField(style={"input_type": "password"})
    new_password = serializers.CharField(min_length=8, style={"input_type": "password"})
    confirm_password = serializers.CharField(style={"input_type": "password"})

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate(self, attrs):
        # The original compared the *old* password against the stored hash and
        # then saved whatever was in the confirm field, so the two new-password
        # inputs were never actually compared to each other.
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The two passwords do not match."}
            )
        try:
            validate_password(attrs["new_password"], self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": list(exc.messages)}
            ) from exc
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "address",
            "city",
            "state",
            "country",
            "zip_code",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
