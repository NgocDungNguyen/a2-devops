"""Routes mounted at /api/auth/.

The token lifecycle in four endpoints:

    register/  -> create an account, and hand back a token pair
    login/     -> exchange email and password for an access + refresh token
    refresh/   -> exchange a refresh token for a new access token
    logout/    -> blacklist the refresh token so it cannot be used again

Access tokens are short-lived (an hour by default) and are sent on every
request; refresh tokens last a week and are only ever sent here. That is what
makes a leaked access token a small problem and a leaked refresh token a large
one. The SPA does this dance automatically in client/src/api/http.js — read
that file alongside this one.

`refresh/` is SimpleJWT's own view, used unchanged. The others are ours only
because they do something extra: send an email, blacklist a token, or apply
Django's password validators.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordForgotView,
    PasswordResetView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("password/forgot/", PasswordForgotView.as_view(), name="auth-password-forgot"),
    path("password/reset/", PasswordResetView.as_view(), name="auth-password-reset"),
    path("password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
]
