"""Seller applications and approved merchant accounts."""

from django.db import models

from apps.core.models import TimeStampedModel


class MerchantStatus(models.TextChoices):
    WAITING = "waiting", "Waiting Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Merchant(TimeStampedModel):
    """A seller, from initial application through to an active storefront.

    Lifecycle:
        1. Someone submits the /sell form      -> status=waiting, is_active=False
        2. An admin approves                   -> status=approved, is_active=True,
                                                  a User with the merchant role and a
                                                  Brand are created
        3. The seller accepts the invitation   -> sets their password, can sign in
        4. An admin may deactivate at any time -> is_active=False, brand deactivated
    """

    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=32, blank=True)
    brand_name = models.CharField(max_length=120, blank=True)
    business = models.TextField(blank=True)

    is_active = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=MerchantStatus.choices,
        default=MerchantStatus.WAITING,
        db_index=True,
    )

    # Declared once, here. The MERN app kept pointers in both directions
    # (Merchant.brand and Brand.merchant) and synchronised them by hand in two
    # different route files, so they could disagree. One OneToOneField with a
    # related_name gives both `merchant.brand` and `brand.merchant` from a
    # single source of truth.
    brand = models.OneToOneField(
        "catalog.Brand",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="merchant",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.brand_name or 'no brand'})"
