"""
Test settings.

Loaded by setting DJANGO_SETTINGS_MODULE=config.settings.test (pytest.ini does
this automatically; the Jenkinsfile's test stage sets it explicitly for
`manage.py test` as a fallback). Optimised for a CI runner rather than a
laptop:

- SQLite in memory, regardless of what DATABASE_URL points at. The test suite
  never touches the real Postgres database, so it can run on a laptop with no
  database installed at all and inside a Jenkins agent with no service
  container wired up yet.
- The MD5 password hasher. PBKDF2 (the production default) is deliberately
  slow; hashing a password for every test user in an authorization-matrix
  suite adds real seconds for no security benefit in a throwaway database.
- Throttling switched off. DEFAULT_THROTTLE_CLASSES exists to stop a *person*
  hammering /api/auth/login/; a test suite that authenticates as four
  different roles per test would trip it by the twentieth test and start
  failing for a reason that has nothing to do with the code under test.
- Email captured in memory (`django.core.mail.outbox`) instead of printed to
  a console nobody is reading during a CI run, so tests that trigger a
  notification (checkout, registration) can assert on it if they want to.
"""

from .base import *  # noqa: F401,F403
from .base import BASE_DIR, REST_FRAMEWORK

DEBUG = False
ALLOWED_HOSTS = ["*"]
SECRET_KEY = "test-only-secret-key-never-used-outside-ci"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MEDIA_ROOT = BASE_DIR / "test_media"

REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": ()}

CORS_ALLOW_ALL_ORIGINS = True

# Pinned rather than inherited from the environment, so the arithmetic in
# test_pricing_unit.py and test_checkout_integration.py (which reproduces the
# worked example in the README's Journey B) is correct regardless of what a
# developer's local .env happens to set.
SALES_TAX_RATE = 0.05
