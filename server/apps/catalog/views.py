"""Catalog endpoints — the public storefront and the management CRUD."""

from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import Brand, Category, Product
from apps.catalog.serializers import (
    BrandManageSerializer,
    BrandSerializer,
    CategoryManageSerializer,
    CategorySerializer,
    ProductManageSerializer,
    ProductSuggestionSerializer,
    SelectOptionSerializer,
    StoreProductDetailSerializer,
    StoreProductSerializer,
)
from apps.catalog.services import (
    deactivate_brand_products,
    deactivate_category_products,
    detach_merchant_from_brand,
)
from apps.core.pagination import LargePagination
from apps.core.permissions import (
    IsAdmin,
    IsAdminOrMerchant,
    MerchantScopedQuerysetMixin,
)

# Sorting is a fixed whitelist. The application this replaces accepted a
# JSON-encoded Mongo sort document straight from the query string, which let
# the client name any field it liked as a sort key.
ORDERING_WHITELIST = {
    "newest": "-created_at",
    "oldest": "created_at",
    "price_asc": "price",
    "price_desc": "-price",
    "rating": "-rating_avg",
    "name": "name",
}
DEFAULT_ORDERING = "newest"


# ---------------------------------------------------------------------------
# Public storefront
# ---------------------------------------------------------------------------


@extend_schema(
    tags=["storefront"],
    parameters=[
        OpenApiParameter("category", str, description="Category slug"),
        OpenApiParameter("brand", str, description="Brand slug"),
        OpenApiParameter("min_price", float),
        OpenApiParameter("max_price", float),
        OpenApiParameter("min_rating", int, description="0-5"),
        OpenApiParameter("search", str, description="Match against the product name"),
        OpenApiParameter(
            "ordering",
            str,
            description="One of: " + ", ".join(ORDERING_WHITELIST),
        ),
    ],
)
class StoreProductListView(ListAPIView):
    """GET /api/products/ — the shop grid.

    Optionally authenticated: a valid token adds an `is_liked` flag to each
    product so the wishlist hearts render filled. Anonymous callers get the
    same list with `is_liked: false`. DRF populates request.user from a
    *verified* token, so unlike the original there is no way to have the
    wishlist join run against a user id from a forged one.
    """

    serializer_class = StoreProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        from apps.reviews.models import Wishlist

        params = self.request.query_params
        qs = (
            Product.objects.storefront()
            .select_related("brand")
            .with_ratings()
        )

        category = params.get("category")
        if category:
            qs = qs.filter(categories__slug=category, categories__is_active=True)

        brand = params.get("brand")
        if brand:
            qs = qs.filter(brand__slug=brand)

        search = params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        for param, lookup in (("min_price", "price__gte"), ("max_price", "price__lte")):
            raw = params.get(param)
            if raw not in (None, ""):
                try:
                    qs = qs.filter(**{lookup: float(raw)})
                except (TypeError, ValueError):
                    pass

        min_rating = params.get("min_rating")
        if min_rating not in (None, "", "0"):
            try:
                # Filtering on an annotation compiles to HAVING, which is what
                # makes "average rating of 4 or more" possible in one query.
                qs = qs.filter(rating_avg__gte=float(min_rating))
            except (TypeError, ValueError):
                pass

        user = self.request.user
        if user.is_authenticated:
            qs = qs.annotate(
                is_liked=Exists(
                    Wishlist.objects.filter(
                        user=user, product=OuterRef("pk"), is_liked=True
                    )
                )
            )
        else:
            qs = qs.annotate(is_liked=Value(False, output_field=BooleanField()))

        ordering = ORDERING_WHITELIST.get(
            params.get("ordering", DEFAULT_ORDERING), ORDERING_WHITELIST[DEFAULT_ORDERING]
        )
        # The trailing "pk" is a tiebreaker. Without it, paginating a sort with
        # many equal values (several products at the same price) can show the
        # same item on two pages and skip another.
        # distinct() is required because the category join can match a product
        # more than once.
        return qs.order_by(ordering, "pk").distinct()


@extend_schema(tags=["storefront"])
class StoreProductDetailView(RetrieveAPIView):
    """GET /api/products/{slug}/"""

    serializer_class = StoreProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        from apps.reviews.models import Wishlist

        qs = (
            Product.objects.storefront()
            .select_related("brand")
            .prefetch_related("categories")
            .with_ratings()
        )
        user = self.request.user
        if user.is_authenticated:
            return qs.annotate(
                is_liked=Exists(
                    Wishlist.objects.filter(
                        user=user, product=OuterRef("pk"), is_liked=True
                    )
                )
            )
        return qs.annotate(is_liked=Value(False, output_field=BooleanField()))


@extend_schema(
    tags=["storefront"],
    parameters=[OpenApiParameter("q", str, description="Search term")],
)
class ProductSearchView(ListAPIView):
    """GET /api/products/search/?q= — navbar autosuggest."""

    serializer_class = ProductSuggestionSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        term = (self.request.query_params.get("q") or "").strip()
        if not term:
            return Product.objects.none()
        return Product.objects.storefront().filter(name__icontains=term)[:10]


@extend_schema(tags=["storefront"])
class PublicCategoryListView(ListAPIView):
    """GET /api/categories/ — active categories, for the nav drawer."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(is_active=True).annotate(
            product_count=Count("products", filter=Q(products__is_active=True))
        )


@extend_schema(tags=["storefront"])
class PublicBrandListView(ListAPIView):
    """GET /api/brands/ — active brands, for the brands page."""

    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Brand.objects.filter(is_active=True).annotate(
            product_count=Count("products", filter=Q(products__is_active=True))
        )


# ---------------------------------------------------------------------------
# Management (/api/manage/...)
# ---------------------------------------------------------------------------


@extend_schema(tags=["manage: products"])
class ManageProductViewSet(MerchantScopedQuerysetMixin, viewsets.ModelViewSet):
    """/api/manage/products/ — admin sees everything, a merchant sees their own."""

    serializer_class = ProductManageSerializer
    permission_classes = [IsAdminOrMerchant]
    pagination_class = LargePagination
    queryset = (
        Product.objects.all().select_related("brand").prefetch_related("categories")
    )
    merchant_scope_field = "brand__merchant__user"

    @action(detail=False, methods=["get"], url_path="select")
    def select(self, request):
        """`[{id, name}]` for the category editor's product picker."""
        products = self.filter_queryset(self.get_queryset()).values("id", "name")
        return Response(SelectOptionSerializer(products, many=True).data)

    def perform_update(self, serializer):
        product = serializer.save()
        return product


@extend_schema(tags=["manage: categories"])
class ManageCategoryViewSet(viewsets.ModelViewSet):
    """/api/manage/categories/ — administrators only."""

    serializer_class = CategoryManageSerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination
    queryset = Category.objects.all().prefetch_related("products")

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        category = serializer.save()
        # Switching a category off takes its products off the shop with it.
        if was_active and not category.is_active:
            deactivate_category_products(category)


@extend_schema(tags=["manage: brands"])
class ManageBrandViewSet(MerchantScopedQuerysetMixin, viewsets.ModelViewSet):
    """/api/manage/brands/

    Merchants may view and edit their own brand. Only administrators may
    create a new one or delete an existing one — a brand is created for a
    seller automatically when their application is approved.
    """

    serializer_class = BrandManageSerializer
    permission_classes = [IsAdminOrMerchant]
    pagination_class = LargePagination
    queryset = Brand.objects.all().select_related("merchant")
    merchant_scope_field = "merchant__user"

    def get_permissions(self):
        if self.action in {"create", "destroy"}:
            return [IsAdmin()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="select")
    def select(self, request):
        brands = self.filter_queryset(self.get_queryset()).values("id", "name")
        return Response(SelectOptionSerializer(brands, many=True).data)

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        brand = serializer.save()
        if was_active and not brand.is_active:
            deactivate_brand_products(brand)

    def perform_destroy(self, instance):
        detach_merchant_from_brand(instance)
        instance.delete()
