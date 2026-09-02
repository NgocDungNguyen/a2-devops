"""
Root URL configuration.

Layout:
    /admin/       Django admin — free CRUD over every model, useful for
                  debugging a deployment without the SPA.
    /healthz/     Liveness probe   (deliberately outside /api/)
    /readyz/      Readiness probe  (deliberately outside /api/)
    /api/         Everything the SPA talks to
    /api/docs/    Swagger UI

Health probes sit at the root rather than under /api/ on purpose: they must
not depend on the API's authentication stack, DRF content negotiation, or the
/api prefix surviving a reverse-proxy rewrite.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from apps.core.views import ActivityMetricsView, HealthzView, ReadyzView

urlpatterns = [
    path("admin/", admin.site.urls),
    # --- probes ---
    path("healthz/", HealthzView.as_view(), name="healthz"),
    path("readyz/", ReadyzView.as_view(), name="readyz"),
    # --- monitoring (outside /api/ for the same reason the probes are) ---
    path("metrics/activity/", ActivityMetricsView.as_view(), name="metrics-activity"),
    # --- api ---
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.accounts.urls_auth")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.catalog.urls")),
    path("api/", include("apps.merchants.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/", include("apps.reviews.urls")),
    # --- schema ---
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# In development Django serves uploaded product images itself. In production
# that job belongs to nginx, S3 or CloudFront — never to the WSGI process.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "RMIT Store administration"
admin.site.site_title = "RMIT Store"
admin.site.index_title = "Store management"
