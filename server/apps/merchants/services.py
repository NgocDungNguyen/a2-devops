"""
The seller lifecycle: apply, approve, invite, accept, deactivate.

Ported from routes/api/merchant.js in the MERN app (createMerchantUser,
createMerchantBrand, deactivateBrand), with the missing authorisation checks
added at the view layer and the hand-rolled reset token replaced by a signed,
self-expiring one.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction

from apps.accounts.models import Role
from apps.catalog.models import Brand
from apps.core.emails import send_templated_mail
from apps.merchants.models import MerchantStatus

User = get_user_model()

# A separate salt from the password-reset generator on purpose: an invitation
# needs to stay valid for about a week while a password reset should expire
# within the hour, and sharing a generator would force one lifetime on both.
INVITE_SALT = "merchant-invite"


def make_invite_token(merchant):
    """Sign the merchant id into a URL-safe, timestamped token."""
    return signing.TimestampSigner(salt=INVITE_SALT).sign(str(merchant.pk))


def read_invite_token(token, max_age=None):
    """Return the merchant id carried by a token, or None if it is not valid.

    Covers tampering, an unknown signature and expiry in one place, so callers
    can return a single friendly error rather than crashing on a null lookup
    the way the original did.
    """
    if max_age is None:
        max_age = settings.MERCHANT_INVITE_MAX_AGE
    try:
        raw = signing.TimestampSigner(salt=INVITE_SALT).unsign(token, max_age=max_age)
        return int(raw)
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return None


def create_brand_for_merchant(merchant):
    """Create the seller's brand and link it, if it does not exist yet.

    The brand starts inactive, matching the original. An administrator has to
    activate it before the merchant's products appear in the shop — surprising
    the first time you meet it, so it is called out in the README.
    """
    if merchant.brand_id:
        return merchant.brand

    brand = Brand.objects.create(
        name=merchant.brand_name or merchant.name,
        description=merchant.business,
        is_active=False,
    )
    merchant.brand = brand
    merchant.save(update_fields=["brand", "updated_at"])
    return brand


@transaction.atomic
def approve_merchant(merchant):
    """Approve an application.

    Two paths, both from the original:
      * the applicant already has a store account — promote it, create the
        brand immediately, and send a welcome note;
      * they do not — create a passwordless account and email an invitation
        link so they can choose a password.

    Returns (merchant, invite_token_or_None).
    """
    merchant.status = MerchantStatus.APPROVED
    merchant.is_active = True
    merchant.save(update_fields=["status", "is_active", "updated_at"])

    existing = User.objects.filter(email__iexact=merchant.email).first()

    if existing:
        existing.role = Role.MERCHANT
        existing.merchant = merchant
        existing.save(update_fields=["role", "merchant", "updated_at"])
        brand = create_brand_for_merchant(merchant)
        send_templated_mail(
            to=[merchant.email],
            template_name="merchant_welcome",
            subject="Your RMIT Store seller account is ready",
            context={"merchant": merchant, "brand": brand, "user": existing},
        )
        return merchant, None

    user = User.objects.create_user(
        email=merchant.email,
        password=None,  # unusable until the invitation is accepted
        first_name=merchant.name,
        role=Role.MERCHANT,
    )
    user.merchant = merchant
    user.save(update_fields=["merchant", "updated_at"])

    token = make_invite_token(merchant)
    send_templated_mail(
        to=[merchant.email],
        template_name="merchant_signup",
        subject="Set up your RMIT Store seller account",
        context={
            "merchant": merchant,
            "signup_link": f"{settings.CLIENT_URL}/merchant-signup/{token}",
        },
    )
    return merchant, token


@transaction.atomic
def reject_merchant(merchant):
    merchant.status = MerchantStatus.REJECTED
    merchant.is_active = False
    merchant.save(update_fields=["status", "is_active", "updated_at"])
    return merchant


@transaction.atomic
def set_merchant_active(merchant, is_active):
    """Enable or disable a seller, taking their brand with them."""
    merchant.is_active = is_active
    merchant.save(update_fields=["is_active", "updated_at"])

    if merchant.brand_id:
        brand = merchant.brand
        brand.is_active = is_active
        brand.save(update_fields=["is_active", "updated_at"])
        if not is_active:
            brand.products.update(is_active=False)

    if not is_active:
        send_templated_mail(
            to=[merchant.email],
            template_name="merchant_deactivate_account",
            subject="Your RMIT Store seller account has been deactivated",
            context={"merchant": merchant},
        )
    return merchant


@transaction.atomic
def complete_merchant_signup(merchant, password, first_name="", last_name=""):
    """Accept an invitation: set the password and create the brand."""
    user = User.objects.filter(email__iexact=merchant.email).first()
    if user is None:
        user = User.objects.create_user(
            email=merchant.email, password=None, role=Role.MERCHANT
        )
        user.merchant = merchant
        user.save(update_fields=["merchant", "updated_at"])

    user.set_password(password)
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.role = Role.MERCHANT
    user.merchant = merchant
    user.save()

    create_brand_for_merchant(merchant)
    return user
