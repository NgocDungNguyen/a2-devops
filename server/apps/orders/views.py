"""Order endpoints."""

from django.db.models import Prefetch, Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.core.emails import send_templated_mail
from apps.core.pagination import LargePagination
from apps.orders.models import Order, OrderItem, OrderItemStatus
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderItemStatusSerializer,
    OrderListSerializer,
    OrderSerializer,
)
from apps.orders.services import cancel_order, create_order, set_item_status


@extend_schema(tags=["orders"])
class OrderViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    """/api/orders/

    Administrators see every order; everybody else sees only their own. This
    scoping is the fix for an endpoint that was authenticated but not
    authorised in the original, letting any signed-in member page through the
    entire order history of the store.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = LargePagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        qs = Order.objects.select_related("user").prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        )
        user = self.request.user
        if user.role != Role.ADMIN:
            qs = qs.filter(user=user)

        search = self.request.query_params.get("search")
        if search:
            # Order numbers are integers now, so "search" means "jump to this
            # order number" rather than the original's ObjectId matching.
            if search.isdigit():
                qs = qs.filter(pk=int(search))
            else:
                qs = qs.none()

        if self.action == "list":
            # Sum() forces a GROUP BY over the joined `items` table, which is
            # what makes Django lose track of whether the queryset is still
            # ordered by Order.Meta's default ("-created_at") — DRF's
            # paginator can no longer tell and warns on every request. The
            # ordering itself was never actually lost; this just says so
            # explicitly instead of relying on the model default surviving
            # an aggregate annotation.
            qs = qs.annotate(item_count=Sum("items__quantity")).order_by("-created_at")

        return qs

    @extend_schema(
        parameters=[OpenApiParameter("search", str, description="Order number")]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(request=OrderCreateSerializer, responses={201: OrderSerializer})
    def create(self, request):
        """POST /api/orders/ — place an order."""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order(
            user=request.user,
            items=serializer.validated_data["items"],
            payment=serializer.validated_data["payment"],
            request=request,
        )

        send_templated_mail(
            to=[request.user.email],
            template_name="order_confirmation",
            subject=f"Your RMIT Store order #{order.pk}",
            context={"order": order, "user": request.user},
        )
        # Plan F exercise: sending this inline adds the mail server's latency
        # to every checkout. Moving it onto a queue (Celery + Redis, or SQS)
        # is a worthwhile later exercise.

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """POST /api/orders/{id}/cancel/ — cancel a whole order."""
        order = self.get_object()
        cancel_order(order)
        order.refresh_from_db()
        return Response(OrderSerializer(order, context={"request": request}).data)

    @extend_schema(request=OrderItemStatusSerializer, responses={200: OrderSerializer})
    @action(
        detail=True,
        methods=["patch"],
        url_path=r"items/(?P<item_id>\d+)",
    )
    def update_item(self, request, pk=None, item_id=None):
        """PATCH /api/orders/{id}/items/{item_id}/ — change a line's status.

        The item is looked up through the order, which is itself scoped to the
        caller, so there is no way to reach somebody else's line item by
        guessing an id — which the original permitted.
        """
        order = self.get_object()
        item = get_object_or_404(OrderItem, pk=item_id, order=order)

        serializer = OrderItemStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        # Customers may cancel; only staff move an item through fulfilment.
        if request.user.role != Role.ADMIN and new_status != OrderItemStatus.CANCELLED:
            raise PermissionDenied(
                "You can only cancel an item. Fulfilment status is set by the store."
            )

        set_item_status(order, item, new_status)
        order.refresh_from_db()
        return Response(OrderSerializer(order, context={"request": request}).data)
