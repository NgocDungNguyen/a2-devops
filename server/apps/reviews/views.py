"""Review and wishlist endpoints."""

from django.db.models import Avg, Count
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product
from apps.core.pagination import LargePagination, StandardPagination
from apps.core.permissions import IsAdmin, IsOwnerOrAdmin
from apps.reviews.models import Review, ReviewStatus, Wishlist
from apps.reviews.serializers import (
    ModerationReviewSerializer,
    ReviewSerializer,
    WishlistSerializer,
    WishlistToggleSerializer,
)


def review_summary(product):
    """Average, totals and the per-star breakdown behind the rating bars.

    Computed in two small aggregate queries rather than in the browser. The
    original built this client-side from a page of reviews, which meant the
    summary disagreed with the stars on the shop card as soon as there were
    more reviews than fitted on one page.
    """
    approved = Review.objects.filter(product=product, status=ReviewStatus.APPROVED)
    totals = approved.aggregate(average=Avg("rating"), total=Count("id"))
    breakdown = {str(star): 0 for star in range(1, 6)}
    for row in approved.values("rating").annotate(count=Count("id")):
        breakdown[str(row["rating"])] = row["count"]

    return {
        "average": round(totals["average"] or 0, 2),
        "total_reviews": totals["total"] or 0,
        "breakdown": breakdown,
    }


@extend_schema(tags=["reviews"])
class ProductReviewListView(ListAPIView):
    """GET /api/products/{slug}/reviews/ — approved reviews plus the summary."""

    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination

    def get_queryset(self):
        # The schema generator instantiates the view without URL kwargs.
        if getattr(self, "swagger_fake_view", False) or "slug" not in self.kwargs:
            return Review.objects.none()
        product = get_object_or_404(Product, slug=self.kwargs["slug"])
        return Review.objects.filter(
            product=product, status=ReviewStatus.APPROVED
        ).select_related("user")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        product = get_object_or_404(Product, slug=self.kwargs["slug"])
        response.data["summary"] = review_summary(product)
        return response


@extend_schema(tags=["reviews"])
class ReviewViewSet(
    CreateModelMixin, UpdateModelMixin, DestroyModelMixin, viewsets.GenericViewSet
):
    """/api/reviews/ — write, edit or remove your own review.

    Editing and deleting were completely unauthenticated in the original:
    anyone could rewrite or delete any review on the store.
    """

    queryset = Review.objects.select_related("user", "product")
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        # New reviews are visible straight away, matching the behaviour of the
        # app this replaces. Admins can reject one from the moderation queue.
        serializer.save(user=self.request.user, status=ReviewStatus.APPROVED)


@extend_schema(tags=["manage: reviews"])
class ManageReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/manage/reviews/ — the moderation queue."""

    queryset = Review.objects.select_related("user", "product").all()
    serializer_class = ModerationReviewSerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter in dict(ReviewStatus.choices):
            qs = qs.filter(status=status_filter)
        return qs

    def _set_status(self, request, pk, new_status):
        review = self.get_object()
        review.status = new_status
        review.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(review).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._set_status(request, pk, ReviewStatus.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set_status(request, pk, ReviewStatus.REJECTED)


@extend_schema(tags=["wishlist"])
class WishlistView(APIView):
    """/api/wishlist/ — GET the list, POST to toggle one product."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):  # for drf-spectacular
        return WishlistSerializer

    @extend_schema(responses={200: WishlistSerializer(many=True)})
    def get(self, request):
        items = (
            Wishlist.objects.filter(user=request.user, is_liked=True)
            .select_related("product")
            .order_by("-updated_at")
        )
        return Response(
            WishlistSerializer(items, many=True, context={"request": request}).data
        )

    @extend_schema(
        request=WishlistToggleSerializer, responses={200: WishlistSerializer}
    )
    def post(self, request):
        serializer = WishlistToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # update_or_create against the unique (user, product) constraint —
        # the original emulated this by hand and could race into duplicates.
        item, _created = Wishlist.objects.update_or_create(
            user=request.user,
            product=serializer.validated_data["product"],
            defaults={"is_liked": serializer.validated_data["is_liked"]},
        )
        return Response(
            WishlistSerializer(item, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
