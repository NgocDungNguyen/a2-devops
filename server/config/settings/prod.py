"""
Production settings.

Activate with:  DJANGO_SETTINGS_MODULE=config.settings.prod

Read this file next to dev.py — the diff between the two is the whole lesson
about what actually changes between environments.
"""

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, env

DEBUG = False

# --- Fail fast, at boot, not at the first request --------------------------
# A missing SECRET_KEY or ALLOWED_HOSTS in production is a deployment failure.
# Better for the process to refuse to start (so the health check never passes,
# so the rollout halts and the old version keeps serving) than to boot and
# quietly serve 500s or run with a known-public dev key.
if SECRET_KEY == "dev-only-insecure-key-change-me-before-you-deploy-anywhere":  # noqa: F405
    raise RuntimeError(
        "SECRET_KEY must be set to a unique value in production. "
        "Generate one with: python -c "
        "'from django.core.management.utils import get_random_secret_key;"
        "print(get_random_secret_key())'"
    )

if not env.list("ALLOWED_HOSTS", default=[]):
    raise RuntimeError(
        "ALLOWED_HOSTS must be set in production, e.g. "
        "ALLOWED_HOSTS=store.example.com,10.0.1.42"
    )

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# --- Behind a load balancer ------------------------------------------------
# An ALB terminates TLS and forwards plain HTTP. Without these two settings
# Django thinks every request is insecure, so SECURE_SSL_REDIRECT loops and
# request.build_absolute_uri() emits http:// links.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Set SECURE_SSL_REDIRECT=false while you are still on plain HTTP, otherwise
# every request redirects to an https:// URL nothing is listening on.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
X_FRAME_OPTIONS = "DENY"

# JSON only. The browsable API renders templates and reflects request data;
# there is no reason to expose it in production.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
)
