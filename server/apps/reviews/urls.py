"""Routes for reviews and the wishlist, mounted at /api/.

Two things are worth understanding here, because the same pattern is used by
catalog, orders and merchants.

**Routers.** `router.register("reviews", ReviewViewSet)` generates the whole
set of REST URLs for a viewset in one line — /reviews/ for the list and
create, /reviews/{id}/ for retrieve, update and delete, plus a route for every
@action on the class. The names it generates come from `basename`:
"review-list", "review-detail", and that is what tests reverse().

**Two routers on purpose.** The customer-facing viewset and the moderation
viewset are separate classes behind separate prefixes, so /api/reviews/ and
/api/manage/reviews/ have entirely different permission classes. Keeping the
staff surface at its own prefix means an endpoint cannot accidentally inherit
the public one's permissions — the split is visible in the URL, not buried in
an if-statement inside a shared view.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.reviews.views import (
    ManageReviewViewSet,
    ProductReviewListView,
    ReviewViewSet,
    WishlistView,
)

router = DefaultRouter()
router.register("reviews", ReviewViewSet, basename="review")

manage_router = DefaultRouter()
manage_router.register("reviews", ManageReviewViewSet, basename="manage-review")

urlpatterns = [
    path(
        "products/<slug:slug>/reviews/",
        ProductReviewListView.as_view(),
        name="product-reviews",
    ),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("", include(router.urls)),
    path("manage/", include(manage_router.urls)),
]
