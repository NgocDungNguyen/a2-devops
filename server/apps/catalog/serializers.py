"""Catalog serializers — public storefront shapes and management shapes."""

from rest_framework import serializers

from apps.catalog.models import Brand, Category, Product
from apps.core.serializers import absolute_media_url


class ImageUrlMixin:
    """Adds an `image_url` that resolves from any host."""

    def get_image_url(self, obj) -> str | None:
        return absolute_media_url(self.context.get("request"), obj.image)


# ---------------------------------------------------------------------------
# Brands
# ---------------------------------------------------------------------------


class BrandSerializer(serializers.ModelSerializer):
    """Public brand card."""

    product_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "description", "is_active", "product_count"]
        read_only_fields = fields


class BrandManageSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(
        source="merchant.name", read_only=True, default=None
    )

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "merchant_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "merchant_name", "created_at", "updated_at"]


class SelectOptionSerializer(serializers.Serializer):
    """`[{id, name}]` for dropdowns."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "is_active", "product_count"]
        read_only_fields = fields


class CategoryManageSerializer(serializers.ModelSerializer):
    """Admin category editor, including the product multi-select."""

    products = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Product.objects.all(), required=False
    )

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "products",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class StoreProductSerializer(ImageUrlMixin, serializers.ModelSerializer):
    """A product card on the shop grid."""

    image_url = serializers.SerializerMethodField()
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    brand_slug = serializers.CharField(source="brand.slug", read_only=True, default=None)
    # Supplied by ProductQuerySet.with_ratings(); the defaults keep the
    # serializer usable on a plain queryset (for example in tests).
    rating_avg = serializers.FloatField(read_only=True, default=0)
    rating_count = serializers.IntegerField(read_only=True, default=0)
    is_liked = serializers.BooleanField(read_only=True, default=False)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "slug",
            "price",
            "image_url",
            "brand_name",
            "brand_slug",
            "rating_avg",
            "rating_count",
            "is_liked",
            "in_stock",
            "quantity",
        ]
        read_only_fields = fields


class StoreProductDetailSerializer(StoreProductSerializer):
    """The product detail page."""

    categories = CategorySerializer(many=True, read_only=True)

    class Meta(StoreProductSerializer.Meta):
        fields = StoreProductSerializer.Meta.fields + [
            "description",
            "taxable",
            "categories",
            "created_at",
        ]
        read_only_fields = fields


class ProductSuggestionSerializer(ImageUrlMixin, serializers.ModelSerializer):
    """The lightweight shape behind the navbar's autosuggest."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "image_url"]
        read_only_fields = fields


class ProductManageSerializer(ImageUrlMixin, serializers.ModelSerializer):
    """Create/edit form for admins and merchants."""

    image_url = serializers.SerializerMethodField()
    image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), required=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "slug",
            "description",
            "image",
            "image_url",
            "quantity",
            "price",
            "taxable",
            "is_active",
            "brand",
            "brand_name",
            "categories",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "image_url", "brand_name", "created_at", "updated_at"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_brand(self, value):
        """A merchant may only file products under their own brand."""
        from apps.accounts.models import Role

        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return value
        if request.user.role != Role.MERCHANT:
            return value

        merchant = getattr(request.user, "merchant", None)
        own_brand = getattr(merchant, "brand", None)
        if own_brand is None:
            raise serializers.ValidationError(
                "Your seller account does not have a brand yet. "
                "Ask an administrator to set one up."
            )
        if value is not None and value.pk != own_brand.pk:
            raise serializers.ValidationError(
                "You can only add products to your own brand."
            )
        return own_brand

    def create(self, validated_data):
        from apps.accounts.models import Role

        request = self.context.get("request")
        # Merchants never choose a brand — theirs is implied.
        if (
            request is not None
            and request.user.is_authenticated
            and request.user.role == Role.MERCHANT
            and not validated_data.get("brand")
        ):
            merchant = getattr(request.user, "merchant", None)
            validated_data["brand"] = getattr(merchant, "brand", None)
        return super().create(validated_data)
