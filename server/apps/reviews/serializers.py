"""Review and wishlist serializers.

A serializer is the layer between JSON and the database. It does three jobs,
and it is worth being able to name them separately:

  * **validation** - `validate_<field>` methods and the field types themselves
    reject bad input before it reaches a model
  * **deserialization** - turning the request body into `validated_data`
  * **serialization** - turning model instances back into JSON for a response

`ModelSerializer` reads the field list off the model, so `fields` is usually
all you have to write. `read_only_fields` is the safety catch: a field listed
there is sent *out* but ignored on the way *in*, which is what stops a client
POSTing `{"status": "approved"}` and moderating its own review. Getting that
list wrong is the single easiest way to open a hole in a DRF application, so
read it carefully in every serializer here.

This file also shows the two normal ways to add a field that is not a column:
`SerializerMethodField` with a `get_<name>` method for anything computed, and
`source="product.name"` for reaching one hop across a relation.
"""

from rest_framework import serializers

from apps.catalog.models import Product
from apps.core.serializers import absolute_media_url
from apps.reviews.models import Review, Wishlist


class ReviewSerializer(serializers.ModelSerializer):
    """A review as shown on a product page.

    Note what a shopper is *not* given about the person who wrote it: no id,
    no email, no full name. A product page is public, so anything named here
    is published to the internet.
    """

    author_name = serializers.SerializerMethodField()
    author_initial = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "title",
            "rating",
            "review",
            "is_recommended",
            "status",
            "author_name",
            "author_initial",
            "created_at",
        ]
        read_only_fields = ["id", "status", "author_name", "author_initial", "created_at"]

    def get_author_name(self, obj) -> str:
        # Falls back to the part of the email before the @ rather than to the
        # whole address, which would publish it.
        return obj.user.first_name or obj.user.email.split("@")[0]

    def get_author_initial(self, obj) -> str:
        return self.get_author_name(obj)[:1].upper()

    def validate_product(self, value):
        if not value.is_active:
            raise serializers.ValidationError(
                "This product is not available for review."
            )
        return value


class ModerationReviewSerializer(ReviewSerializer):
    """The moderation queue: adds who wrote it and what it is about.

    A separate class rather than a flag on the one above. The extra fields
    here — the author's email in particular — are for staff only, and the way
    they are kept from the public is that the public serializer simply does
    not contain them. A single serializer that hides fields depending on who
    is asking is one forgotten condition away from leaking them.
    """

    author_email = serializers.CharField(source="user.email", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta(ReviewSerializer.Meta):
        fields = ReviewSerializer.Meta.fields + [
            "author_email",
            "product_name",
            "product_slug",
            "product_image",
        ]
        read_only_fields = fields

    def get_product_image(self, obj) -> str | None:
        return absolute_media_url(self.context.get("request"), obj.product.image)


class WishlistSerializer(serializers.ModelSerializer):
    """A wishlist row, with just enough product detail to render the card."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "product",
            "product_name",
            "product_slug",
            "product_price",
            "product_image",
            "is_liked",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "product_name",
            "product_slug",
            "product_price",
            "product_image",
            "updated_at",
        ]

    def get_product_image(self, obj) -> str | None:
        return absolute_media_url(self.context.get("request"), obj.product.image)


class WishlistToggleSerializer(serializers.Serializer):
    """The body of "heart this product".

    A plain `Serializer`, not a ModelSerializer: this describes an *action*,
    not a row. The user is taken from the request rather than the body, so
    there is nothing here to let one account edit another's wishlist.

    `PrimaryKeyRelatedField(queryset=...)` accepts an id and hands the view a
    real Product, rejecting ids that do not exist with a 400 before any code
    of ours runs.
    """

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    is_liked = serializers.BooleanField(default=True)
