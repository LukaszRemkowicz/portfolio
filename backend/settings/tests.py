# backend/core/test_settings.py
"""
Test settings for pytest
"""

import os

from .base import *  # noqa: F401,F403,E402

SECRET_KEY = "test-secret-key-for-pytest"

ADMIN_DOMAIN = "testadmin.local"
API_DOMAIN = "testapi.local"
CSRF_COOKIE_DOMAIN = ".testapi.local"

_test_base_hosts = [SITE_DOMAIN, ADMIN_DOMAIN, API_DOMAIN]  # noqa: F405
ALLOWED_HOSTS = [h for h in _test_base_hosts if h] + ["localhost", "127.0.0.1", "0.0.0.0"]

CORS_ALLOWED_ORIGINS = []
for h in _test_base_hosts:
    if h:
        CORS_ALLOWED_ORIGINS.append(f"https://{h}")
        CORS_ALLOWED_ORIGINS.append(f"http://{h}")
        CORS_ALLOWED_ORIGINS.append(f"http://{h}:3000")
CORS_ALLOWED_ORIGINS = list(set(CORS_ALLOWED_ORIGINS))

CSRF_TRUSTED_ORIGINS = []
for h in _test_base_hosts:
    if h:
        CSRF_TRUSTED_ORIGINS.append(f"https://{h}")
        CSRF_TRUSTED_ORIGINS.append(f"http://{h}")
CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS))

DATABASES["default"]["HOST"] = (  # noqa: F405
    "db" if os.environ.get("DOCKER_ENV") == "true" else "localhost"
)

# Configure test database name
# pytest-django automatically creates a test database with this name
# It will prefix with 'test_' if not specified, but we make it explicit
production_db_name = DATABASES["default"].get("NAME", "portfolio")  # noqa: F405
DATABASES["default"].setdefault("TEST", {}).update(  # noqa: F405
    {
        "NAME": f"test_{production_db_name}",
    }
)

# Use local memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-unique-snowflake",
    },
    "select2": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-select2",
    },
}

# Use console email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SIMULATE_CONTACT_EMAILS = True
DEFAULT_FROM_EMAIL = "tests@portfolio.local"
CONTACT_EMAIL = "owner@portfolio.local"
SESSION_COOKIE_DOMAIN = ".example.com"

# Faster test settings
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Celery test settings
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Disable logging during tests
LOGGING_CONFIG = None
ENABLE_SENTRY = False

# Tests run in HTTP mode by default, do not force SSL redirects
SECURE_SSL_REDIRECT = False

# Use mock LLM provider for all services in tests
TRANSLATION_LLM_PROVIDER = "mock"
MONITORING_LLM_PROVIDER = "mock"
LANDING_PAGE_TOTAL_TIME_SPENT_LLM_PROVIDER = "mock"

PROJECT_OWNER = "owner"
