"""
Role-based permission classes.

The application has three roles, stored on the user record: admin, merchant
and member. They are distinct from Django's is_staff / is_superuser flags,
which only control access to /admin/.

Read this next to the endpoint map in the README: the whole reason management
CRUD lives under /api/manage/ is so the permission class needed for a URL is
obvious from the URL itself.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def _role(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    return user.role


class IsAdmin(BasePermission):
    """Store administrator."""

    message = "You are not allowed to make this request."

    def has_permission(self, request, view):
        from apps.accounts.models import Role

        return _role(request) == Role.ADMIN


class IsMerchant(BasePermission):
    """An approved, currently-active seller.

    A merchant whose account has been deactivated by an admin keeps the role
    but loses access — mirroring the disabled-account screen in the UI.
    """

    message = "Your seller account is not active."

    def has_permission(self, request, view):
        from apps.accounts.models import Role

        if _role(request) != Role.MERCHANT:
            return False
        merchant = getattr(request.user, "merchant", None)
        return bool(merchant and merchant.is_active)


class IsAdminOrMerchant(BasePermission):
    message = "You are not allowed to make this request."

    def has_permission(self, request, view):
        return IsAdmin().has_permission(request, view) or IsMerchant().has_permission(
            request, view
        )


class IsAdminOrReadOnly(BasePermission):
    """Anyone may read; only an admin may write."""

    message = "You are not allowed to make this request."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsAdmin().has_permission(request, view)


class IsOwnerOrAdmin(BasePermission):
    """Object-level: the row's owner, or an admin.

    Expects the object to expose a `user` attribute.
    """

    message = "You are not allowed to make this request."

    def has_object_permission(self, request, view, obj):
        from apps.accounts.models import Role

        if not request.user.is_authenticated:
            return False
        if request.user.role == Role.ADMIN:
            return True
        return getattr(obj, "user_id", None) == request.user.id


class MerchantScopedQuerysetMixin:
    """Narrows a queryset to the requesting merchant's own records.

    Admins see everything. Merchants see only rows belonging to the brand
    their merchant account owns. Set `merchant_scope_field` to the lookup path
    from the model to the owning user.

    Scoping the *queryset* rather than checking ownership in each handler
    means an id belonging to someone else returns 404 rather than 403 — so the
    endpoint cannot be used to probe for which ids exist.
    """

    merchant_scope_field = "brand__merchant__user"

    def get_queryset(self):
        from apps.accounts.models import Role

        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.role == Role.MERCHANT:
            return qs.filter(**{self.merchant_scope_field: user})
        return qs
