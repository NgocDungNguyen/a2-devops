"""
Catalog side effects.

The deactivation cascades are ported from server/utils/store.js and the
deactivateBrand / deactivateMerchant helpers in the MERN routes. They live
here rather than inside a view so the seed command, the Django admin and the
API all get the same behaviour.
"""

from django.db import transaction


@transaction.atomic
def deactivate_brand_products(brand):
    """Hide every product belonging to a brand that has just been switched off."""
    return brand.products.update(is_active=False)


@transaction.atomic
def deactivate_category_products(category):
    """Hide every product in a category that has just been switched off.

    Note this matches the original's behaviour, which is blunt: a product in
    two categories is deactivated when either one is. The tooltip in the admin
    UI warns about it.
    """
    return category.products.update(is_active=False)


@transaction.atomic
def detach_merchant_from_brand(brand):
    """Reset the seller when their brand is deleted.

    The merchant goes back to awaiting approval with no brand attached, which
    is the state a fresh application is in — so an admin can re-approve them
    and a new brand gets created.
    """
    from apps.merchants.models import MerchantStatus

    merchant = getattr(brand, "merchant", None)
    if merchant is None:
        return None
    merchant.brand = None
    merchant.is_active = False
    merchant.status = MerchantStatus.WAITING
    merchant.save(update_fields=["brand", "is_active", "status", "updated_at"])
    return merchant
