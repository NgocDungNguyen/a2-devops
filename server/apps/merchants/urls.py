from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.merchants.views import (
    ManageMerchantViewSet,
    MerchantApplyView,
    MerchantSignupView,
)

manage_router = DefaultRouter()
manage_router.register("merchants", ManageMerchantViewSet, basename="manage-merchant")

urlpatterns = [
    path("merchants/apply/", MerchantApplyView.as_view(), name="merchant-apply"),
    path("merchants/signup/", MerchantSignupView.as_view(), name="merchant-signup"),
    path("manage/", include(manage_router.urls)),
]
