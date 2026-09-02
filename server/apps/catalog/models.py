"""Brands, categories and products."""

from pathlib import Path
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Avg, Count, FloatField, Q, Value
from django.db.models.functions import Coalesce

from apps.core.models import SluggedModel


def product_image_path(instance, filename):
    """Store uploads under a random name.

    The MERN app used the uploaded file's original name as the S3 key, so two
    merchants uploading "photo.jpg" silently overwrote each other's product
    image. A UUID makes collisions impossible.
    """
    suffix = Path(filename).suffix.lower() or ".jpg"
    return f"products/{uuid4().hex}{suffix}"


class Brand(SluggedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(SluggedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def with_ratings(self):
        """Annotate `rating_avg` and `rating_count` from approved reviews.

        Ratings are computed at query time rather than stored on the product.
        A denormalised column would need signal handlers on review create,
        update, delete, approve and reject, and would drift the first time
        somebody edited a review in the Django admin. On a catalogue this size
        the aggregate costs well under a millisecond.

        Note `distinct=True` on the count: without it, joining the category
        many-to-many multiplies the review rows and inflates the total.

        Only approved reviews count. The MERN app averaged over every review
        regardless of status while only *displaying* the approved ones, so the
        stars on a shop card disagreed with the reviews on the product page.

        # Plan F exercise: if the catalogue grows past a few thousand rows,
        # denormalise rating_avg/rating_count onto Product and maintain them
        # with signals, then measure the difference.
        """
        from apps.reviews.models import ReviewStatus

        approved = Q(reviews__status=ReviewStatus.APPROVED)
        return self.annotate(
            rating_count=Count("reviews", filter=approved, distinct=True),
            rating_avg=Coalesce(
                Avg("reviews__rating", filter=approved),
                Value(0.0),
                output_field=FloatField(),
            ),
        )

    def storefront(self):
        """Only what an anonymous shopper is allowed to see."""
        return self.filter(is_active=True).filter(
            Q(brand__isnull=True) | Q(brand__is_active=True)
        )


class Product(SluggedModel):
    slug_source_field = "name"

    sku = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    taxable = models.BooleanField(
        default=False, help_text="Apply sales tax to this product at checkout."
    )
    is_active = models.BooleanField(default=True, db_index=True)

    brand = models.ForeignKey(
        Brand,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
        db_index=True,
    )
    # A real many-to-many, declared on Product but named so that
    # `category.products` still reads exactly like the array it replaces.
    # The MERN app stored this only as an array on Category, which made
    # "which categories is this product in?" unanswerable.
    categories = models.ManyToManyField(Category, blank=True, related_name="products")

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "price"]),
            models.Index(fields=["-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0), name="product_price_non_negative"
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.quantity > 0
