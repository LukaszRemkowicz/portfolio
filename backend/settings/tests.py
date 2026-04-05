# backend/core/test_settings.py
"""
Test settings for pytest
"""

__all__ = [  # noqa: F405
    "DATABASES",
    "CACHES",
    "EMAIL_BACKEND",
    "PASSWORD_HASHERS",
    "LOGGING_CONFIG",
    "SIMULATE_CONTACT_EMAILS",
]

# Set required environment variables BEFORE importing settings
import os

if not os.environ.get("ADMIN_DOMAIN"):
    os.environ["ADMIN_DOMAIN"] = "testadmin.local"
if not os.environ.get("API_DOMAIN"):
    os.environ["API_DOMAIN"] = "testapi.local"
if not os.environ.get("CSRF_COOKIE_DOMAIN"):
    os.environ["CSRF_COOKIE_DOMAIN"] = ".testapi.local"
# Use Docker service discovery when tests run in containers, otherwise localhost.
if os.environ.get("DOCKER_ENV") == "true":
    os.environ.setdefault("DB_HOST", "db")
else:
    os.environ.setdefault("DB_HOST", "localhost")

if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"

from .base import *  # noqa: F401,F403,E402

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
