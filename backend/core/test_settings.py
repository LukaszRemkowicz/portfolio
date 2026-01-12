# backend/core/test_settings.py
"""
Test settings for pytest
"""

from .settings import *  # noqa: F401,F403

# Configure test database name
# pytest-django automatically creates a test database with this name
# It will prefix with 'test_' if not specified, but we make it explicit
production_db_name = DATABASES["default"].get("NAME", "portfolio")  # noqa: F405
DATABASES["default"]["TEST"] = {  # noqa: F405
    "NAME": f"test_{production_db_name}",
}

# Faster test settings
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING_CONFIG = None


DEFAULT_FROM_EMAIL = "test@example.com"
