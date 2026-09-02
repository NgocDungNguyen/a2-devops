"""Catalog routes, mounted at /api/.

Note the two prefixes. Everything under /api/ is public and read-only;
everything under /api/manage/ requires a role. Keeping them apart means the
permission a URL needs is obvious from the URL, which is exactly the property
the original lacked when it overloaded /api/product/ for both audiences and
lost the role check on one of them.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.catalog.views import (
    ManageBrandViewSet,
    ManageCategoryViewSet,
    ManageProductViewSet,
    ProductSearchView,
    PublicBrandListView,
    PublicCategoryListView,
    StoreProductDetailView,
    StoreProductListView,
)

manage_router = DefaultRouter()
manage_router.register("products", ManageProductViewSet, basename="manage-product")
manage_router.register("categories", ManageCategoryViewSet, basename="manage-category")
manage_router.register("brands", ManageBrandViewSet, basename="manage-brand")

urlpatterns = [
    # Public storefront. The /search/ route is declared before the slug route
    # so that "search" is not swallowed as a product slug.
    path("products/search/", ProductSearchView.as_view(), name="product-search"),
    path("products/", StoreProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", StoreProductDetailView.as_view(), name="product-detail"),
    path("categories/", PublicCategoryListView.as_view(), name="category-list"),
    path("brands/", PublicBrandListView.as_view(), name="brand-list"),
    # Management
    path("manage/", include(manage_router.urls)),
]
