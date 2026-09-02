"""Product reviews and wishlist entries."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class ReviewStatus(models.TextChoices):
    WAITING = "waiting", "Waiting Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Review(TimeStampedModel):
    """A customer review.

    New reviews are approved immediately, matching the MERN app's actual
    behaviour (its route handler overrode the schema default). Admins can
    still reject one from the moderation queue, which removes it from the
    product page and from the product's average rating.
    """

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    title = models.CharField(max_length=200)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()
    is_recommended = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.APPROVED,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["product", "status"])]

    def __str__(self):
        return f"{self.rating}★ {self.title}"


class Wishlist(TimeStampedModel):
    """A product a customer has hearted."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    is_liked = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            # The MERN app emulated an upsert with findOneAndUpdate and could
            # race into duplicate rows, which then broke the "is this liked?"
            # lookup on the shop page.
            models.UniqueConstraint(
                fields=["user", "product"], name="uniq_wishlist_user_product"
            )
        ]

    def __str__(self):
        return f"{self.user.email} ♥ {self.product.name}"
