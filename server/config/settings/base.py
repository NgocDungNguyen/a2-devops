"""
Shared settings for the RMIT Store API.

Everything that is the same in every environment lives here. Environment
specific overrides live in dev.py / prod.py / test.py, which all start with
``from .base import *``.

Which module loads is decided by DJANGO_SETTINGS_MODULE — that single
environment variable is how the same code runs on a laptop, an EC2 instance,
and inside a container.
"""

from datetime import timedelta
from pathlib import Path

import environ

# server/config/settings/base.py -> server/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# Read server/.env when it exists. Real deployments usually set process
# environment variables instead, which take precedence over the file.
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key-change-me-before-you-deploy-anywhere")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# The URL the SPA is served from. Used to build password-reset and merchant
# invitation links that land the user back in the frontend.
CLIENT_URL = env("CLIENT_URL", default="http://localhost:5173").rstrip("/")

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Released version + build metadata, surfaced at GET /api/version/ so a
# blue/green or canary rollout can be verified from outside the box.
APP_VERSION = env("APP_VERSION", default="1.0.0")
GIT_COMMIT = env("GIT_COMMIT", default="dev")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.merchants",
    "apps.orders",
    "apps.reviews",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Feeds /metrics/activity/ (the dashboard's "people on the store now").
    # Last on purpose: it observes traffic, it must never gate it.
    "apps.core.middleware.VisitorActivityMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
#
# One DATABASE_URL beats five separate variables: it is what django-environ,
# Docker Compose, Kubernetes secrets and AWS RDS connection strings all speak.
#
#   postgres://USER:PASSWORD@HOST:PORT/NAME

DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default="postgres://rmit:rmit@localhost:5432/rmit_store",
    )
}
# Reuse connections instead of opening one per request. Set to 0 if you put
# PgBouncer in front of RDS.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)


AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Password-reset links stay valid for one hour.
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", default=3600)

# Merchant invitation links stay valid for seven days — an admin approving an
# application should not have to babysit the new seller's inbox.
MERCHANT_INVITE_MAX_AGE = env.int("MERCHANT_INVITE_MAX_AGE", default=60 * 60 * 24 * 7)


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-au"
TIME_ZONE = env("TIME_ZONE", default="Australia/Melbourne")
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# --- Plan F exercise -------------------------------------------------------
# Uploaded product images land on the instance's local disk by default. The
# moment you put two application servers behind a load balancer, half the
# requests for a given image 404 — the file only exists on the box that
# received the upload. Flipping USE_S3 to true moves media to a shared bucket
# and fixes it. Provisioning that bucket plus an IAM instance role is the
# CloudFormation lab.
#
# Note there are deliberately no AWS credentials read here: boto3's default
# credential chain picks up AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from the
# environment locally, and an IAM instance profile (EC2) or IRSA (EKS) in the
# cloud. Instance roles are the correct answer; long-lived keys in a .env file
# are the thing the course is teaching you to stop doing.
# ---------------------------------------------------------------------------
USE_S3 = env.bool("USE_S3", default=False)
if USE_S3:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            "region_name": env("AWS_S3_REGION_NAME", default="ap-southeast-2"),
            "location": "media",
            "file_overwrite": False,
            "querystring_auth": env.bool("AWS_S3_QUERYSTRING_AUTH", default=False),
        },
    }


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Deny by default. Every public endpoint must opt in with an explicit
    # permission_classes = [AllowAny]. The MERN app this replaces leaked user
    # lists, order history and address records purely through *omitted*
    # middleware — a deny-by-default posture makes that class of mistake fail
    # closed instead of open.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": env("THROTTLE_AUTH", default="20/min"),
        "contact": env("THROTTLE_CONTACT", default="5/hour"),
        "merchant_apply": env("THROTTLE_MERCHANT_APPLY", default="5/hour"),
        "newsletter": env("THROTTLE_NEWSLETTER", default="5/hour"),
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    # Short-lived access token keeps the damage window small if one leaks; the
    # refresh token preserves the week-long session the old app had.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "RMIT Store API",
    "DESCRIPTION": (
        "REST API for the RMIT Store — a teaching application for COSC2767 "
        "Systems Deployment and Operations."
    ),
    "VERSION": APP_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",
    # Several models have a "status" field. Naming the choice sets explicitly
    # keeps the generated schema readable instead of producing components
    # called Status125Enum.
    #
    # Merchant and Review share one entry deliberately: their choices are
    # identical (waiting / approved / rejected), so the generator sees a single
    # choice set and giving it two names is an error.
    "ENUM_NAME_OVERRIDES": {
        "ApprovalStatusEnum": "apps.merchants.models.MerchantStatus.choices",
        "OrderStatusEnum": "apps.orders.models.OrderStatus.choices",
        "OrderItemStatusEnum": "apps.orders.models.OrderItemStatus.choices",
        "RoleEnum": "apps.accounts.models.Role.choices",
    },
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
#
# Only needed when the SPA is served from a different origin than the API.
# If you serve the built SPA and proxy /api through one nginx (the simplest
# Plan B/D/E layout), the browser sees a single origin and none of this
# applies. It becomes necessary the moment you split client and server onto
# separate EC2 instances (Plan C).

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = False
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=CORS_ALLOWED_ORIGINS)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
#
# The console backend is the default so a fresh checkout works with zero
# configuration — password-reset and merchant-invitation links are printed
# straight into the runserver log, which is exactly what you need to complete
# those flows locally.
#
# Amazon SES needs no code change, only environment variables:
#   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#   EMAIL_HOST=email-smtp.ap-southeast-2.amazonaws.com

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
# Only read when EMAIL_BACKEND is the file-based backend — a third option
# alongside console (the default) and SMTP/SES, useful when something other
# than a human needs to read a sent message: an E2E test reading a merchant
# invitation link off disk instead of scraping a terminal's stdout. Unused,
# and therefore harmless, with either of the other two backends.
EMAIL_FILE_PATH = env("EMAIL_FILE_PATH", default=str(BASE_DIR / ".dev-emails"))
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="RMIT Store <no-reply@rmit-store.local>"
)
# Where contact-form submissions and merchant applications are forwarded.
STORE_NOTIFICATION_EMAIL = env(
    "STORE_NOTIFICATION_EMAIL", default="store-admin@rmit-store.local"
)


# ---------------------------------------------------------------------------
# Store rules
# ---------------------------------------------------------------------------
#
# Ported from server/config/tax.js in the MERN app: a flat rate applied only
# to products flagged taxable.

SALES_TAX_RATE = env.float("SALES_TAX_RATE", default=0.05)
SALES_TAX_STATE_CODE = env("SALES_TAX_STATE_CODE", default="CA")
SALES_TAX_STATE_NAME = env("SALES_TAX_STATE_NAME", default="California")
STORE_CURRENCY = env("STORE_CURRENCY", default="USD")

# Derived rather than read from the environment on purpose: django-environ
# treats a value beginning with "$" as a reference to another variable, so a
# literal STORE_CURRENCY_SYMBOL=$ in a .env file sends it into infinite
# recursion. Mapping from the currency code sidesteps that entirely.
_CURRENCY_SYMBOLS = {
    "USD": "$",
    "AUD": "$",
    "NZD": "$",
    "CAD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "VND": "₫",
}
STORE_CURRENCY_SYMBOL = _CURRENCY_SYMBOLS.get(STORE_CURRENCY.upper(), STORE_CURRENCY)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = env("LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        # Health probes hit /healthz/ every few seconds. Logging each one
        # buries everything else in the access log.
        "apps.core.health": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
