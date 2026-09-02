"""Routes mounted at /api/ by config/urls.py.

Everything here is small and public — the bits of the API that are not about
any one part of the store. If you are looking for a URL, this file and its
siblings in apps/*/urls.py are the whole map; nothing routes itself.

`name=` on each route is not decoration. Tests and email templates address
endpoints by name (`reverse("public-config")`), so the path can be changed
here without a search-and-replace across the project — and renaming one of
these strings will break tests that a moved path would not.
"""

from django.urls import path

from apps.core.views import (
    ContactCreateView,
    NewsletterSubscribeView,
    PublicConfigView,
    VersionView,
)

urlpatterns = [
    path("config/", PublicConfigView.as_view(), name="public-config"),
    path("version/", VersionView.as_view(), name="version"),
    path("contact/", ContactCreateView.as_view(), name="contact-create"),
    path(
        "newsletter/subscribe/",
        NewsletterSubscribeView.as_view(),
        name="newsletter-subscribe",
    ),
]
