"""
Test settings for pytest
"""

from .settings import *  # noqa: F401,F403

# Override database settings for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_portfolio",
        "USER": "test_user",
        "PASSWORD": "test_password",
        "HOST": "localhost",
        "PORT": "5433",  # Fixed port for test database
    }
}

# Enable migrations - pytest will check them before tests
# MIGRATION_MODULES = DisableMigrations()  # Keep migrations enabled

# Faster test settings
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING_CONFIG = None
