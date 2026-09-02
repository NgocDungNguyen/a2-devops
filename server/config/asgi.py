"""ASGI entry point, for uvicorn/daphne if you prefer them to gunicorn."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
