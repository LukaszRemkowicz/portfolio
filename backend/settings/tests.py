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
]

# Set required environment variables BEFORE importing settings
import os

os.environ.setdefault("ADMIN_DOMAIN", "testadmin.local")
os.environ.setdefault("API_DOMAIN", "testapi.local")
os.environ.setdefault("CSRF_COOKIE_DOMAIN", ".testapi.local")
# Override DB_HOST for local test execution (tests run outside Docker)
os.environ.setdefault("DB_HOST", "localhost")

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

# Faster test settings
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING_CONFIG = None
