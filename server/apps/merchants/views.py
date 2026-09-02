"""Merchant endpoints."""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.serializers import UserSerializer
from apps.accounts.views import _token_pair
from apps.core.emails import send_templated_mail
from apps.core.pagination import LargePagination
from apps.core.permissions import IsAdmin
from apps.merchants.models import Merchant
from apps.merchants.serializers import (
    MerchantApplicationSerializer,
    MerchantSerializer,
    MerchantSignupSerializer,
)
from apps.merchants.services import (
    approve_merchant,
    complete_merchant_signup,
    reject_merchant,
    set_merchant_active,
)


@extend_schema(tags=["merchants"])
class MerchantApplyView(GenericAPIView):
    """POST /api/merchants/apply/ — the public /sell form."""

    serializer_class = MerchantApplicationSerializer
    permission_classes = [AllowAny]
    throttle_scope = "merchant_apply"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = serializer.save()

        send_templated_mail(
            to=[merchant.email],
            template_name="merchant_application",
            subject="We have received your RMIT Store seller application",
            context={"merchant": merchant},
        )
        send_templated_mail(
            to=[settings.STORE_NOTIFICATION_EMAIL],
            template_name="merchant_application",
            subject=f"New seller application: {merchant.brand_name or merchant.name}",
            context={"merchant": merchant},
        )

        return Response(
            {
                "detail": (
                    "Thanks for your interest. We have received your application "
                    "and will be in touch soon."
                ),
                "merchant": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["merchants"])
class MerchantSignupView(GenericAPIView):
    """POST /api/merchants/signup/ — accept an invitation.

    Returns a token pair so the new seller lands signed in, rather than being
    bounced to the login form as the original did.
    """

    serializer_class = MerchantSignupSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = complete_merchant_signup(
            merchant=serializer.validated_data["merchant"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )
        user.refresh_from_db()
        return Response(
            {**_token_pair(user), "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["manage: merchants"])
class ManageMerchantViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """/api/manage/merchants/ — administrators only.

    Every route here is admin-gated. In the original, approve, reject and the
    enable/disable toggle were authenticated but had no role check, so any
    signed-in member could approve themselves as a seller.
    """

    queryset = Merchant.objects.all().select_related("brand")
    serializer_class = MerchantSerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination
    filter_backends = [SearchFilter]
    search_fields = ["name", "email", "phone_number", "brand_name", "status"]

    def perform_update(self, serializer):
        """Only `is_active` is meaningful here, and it cascades to the brand."""
        merchant = serializer.instance
        requested = serializer.validated_data.get("is_active", merchant.is_active)
        if requested != merchant.is_active:
            set_merchant_active(merchant, requested)
        serializer.instance.refresh_from_db()

    def perform_destroy(self, instance):
        if instance.brand_id:
            brand = instance.brand
            brand.is_active = False
            brand.save(update_fields=["is_active", "updated_at"])
        instance.delete()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        merchant = self.get_object()
        merchant, _token = approve_merchant(merchant)
        return Response(self.get_serializer(merchant).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        merchant = reject_merchant(self.get_object())
        return Response(self.get_serializer(merchant).data)
