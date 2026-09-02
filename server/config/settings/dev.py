"""
Development settings.

Loaded by default (see manage.py). Optimised for a laptop: verbose errors,
no host checking, email printed to the terminal, and the DRF browsable API
available so you can click through the whole backend before the Vue app runs.
"""

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, env

DEBUG = True

# Convenient locally and on a scratch EC2 box whose public IP you don't want to
# keep re-typing. prod.py deliberately does NOT do this.
ALLOWED_HOSTS = ["*"]

# Any origin, so `npm run dev` works whether Vite picked 5173, 5174 or 5175.
CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

# The browsable API is the fastest way to exercise an endpoint by hand.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Uncompressed static files, so collectstatic is not required to run the admin.
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}
