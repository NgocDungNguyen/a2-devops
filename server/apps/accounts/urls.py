"""Routes mounted at /api/ — users and addresses."""

from rest_framework.routers import DefaultRouter

from apps.accounts.views import AddressViewSet, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = router.urls
