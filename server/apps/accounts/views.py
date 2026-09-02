"""Authentication, profile and address endpoints."""

from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import Address, Role
from apps.accounts.serializers import (
    AddressSerializer,
    AdminUserSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeUpdateSerializer,
    PasswordChangeSerializer,
    PasswordForgotSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserSerializer,
)
from apps.core.emails import send_templated_mail
from apps.core.models import NewsletterSubscriber
from apps.core.pagination import LargePagination
from apps.core.permissions import IsAdmin

User = get_user_model()


def _token_pair(user):
    """Issue a fresh access/refresh pair for a user we have already verified."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["email"] = user.email
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


@extend_schema(tags=["auth"])
class RegisterView(GenericAPIView):
    """POST /api/auth/register/ — create an account and sign straight in."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_subscribed = serializer.validated_data.get("is_subscribed", False)
        user = serializer.save()

        if is_subscribed:
            NewsletterSubscriber.objects.get_or_create(
                email=user.email, defaults={"is_active": True}
            )

        send_templated_mail(
            to=[user.email],
            template_name="signup",
            subject="Welcome to the RMIT Store",
            context={"user": user},
        )

        return Response(
            {**_token_pair(user), "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["auth"])
class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — exchange email + password for a token pair."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"


@extend_schema(tags=["auth"])
class LogoutView(GenericAPIView):
    """POST /api/auth/logout/ — revoke a refresh token.

    Real revocation, not just clearing localStorage: the token goes on the
    blacklist so a copy captured earlier stops working immediately.
    """

    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            # Already expired or already blacklisted. The caller's intent —
            # "end this session" — is satisfied either way.
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(tags=["auth"])
class PasswordForgotView(GenericAPIView):
    """POST /api/auth/password/forgot/ — email a reset link."""

    serializer_class = PasswordForgotSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user and user.has_usable_password():
            link = PasswordResetSerializer.make_link(user, settings.CLIENT_URL)
            send_templated_mail(
                to=[user.email],
                template_name="password_reset",
                subject="Reset your RMIT Store password",
                context={"user": user, "reset_link": link},
            )

        # Always 200, whether or not the address is registered. Returning 400
        # for an unknown email — as the original did — turns this endpoint
        # into an oracle for testing whether somebody has an account.
        return Response(
            {
                "detail": (
                    "If an account exists for that email address, a password "
                    "reset link is on its way."
                )
            }
        )


@extend_schema(tags=["auth"])
class PasswordResetView(GenericAPIView):
    """POST /api/auth/password/reset/ — complete a reset."""

    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_templated_mail(
            to=[user.email],
            template_name="password_reset_confirmation",
            subject="Your RMIT Store password has been changed",
            context={"user": user},
        )
        return Response({"detail": "Your password has been reset. Please sign in."})


@extend_schema(tags=["auth"])
class PasswordChangeView(GenericAPIView):
    """POST /api/auth/password/change/ — change it while signed in."""

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_templated_mail(
            to=[user.email],
            template_name="password_reset_confirmation",
            subject="Your RMIT Store password has been changed",
            context={"user": user},
        )
        return Response({"detail": "Your password has been changed."})


@extend_schema(tags=["users"])
class UserViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """/api/users/

    Listing every account is an administrator action. The original left this
    endpoint authenticated but unrestricted, so any signed-in member could
    page through every user in the system.
    """

    queryset = User.objects.all().select_related("merchant")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination
    filter_backends = [SearchFilter]
    search_fields = ["first_name", "last_name", "email"]

    def get_permissions(self):
        if self.action in {"me", "update_me"}:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @me.mapping.patch
    def update_me(self, request):
        serializer = MeUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


@extend_schema(tags=["addresses"])
class AddressViewSet(viewsets.ModelViewSet):
    """/api/addresses/ — a customer's own saved addresses.

    Scoping the queryset to the requesting user does the authorisation: an id
    belonging to somebody else is simply not in the queryset, so it returns
    404 rather than 403 and cannot be used to discover which ids exist. In the
    original, three of these five routes had no authentication at all.
    """

    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Roles are exported for the OpenAPI schema and for tests.
ROLE_CHOICES = Role.choices
