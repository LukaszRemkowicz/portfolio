# backend/core/settings.py
import os
from pathlib import Path
from typing import Any, cast

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default=cast(Any, "django-insecure-development-key"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=cast(Any, False))

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[]) + [
    "https://portfolio.local",
    "http://portfolio.local",
    "http://portfolio.local:3000",
]
CORS_ALLOW_CREDENTIALS = True

# Domain settings
ADMIN_DOMAIN = "admin.portfolio.local"
API_DOMAIN = "portfolio.local"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[]) + [
    ADMIN_DOMAIN,
    API_DOMAIN,
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "172.10.0.3",
    "backend",
]

# Custom user model - this needs to be set before INSTALLED_APPS
AUTH_USER_MODEL = "users.User"

# CSRF Settings
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[]) + [
    f"https://{ADMIN_DOMAIN}",
    f"https://{API_DOMAIN}",
]
CSRF_COOKIE_DOMAIN = ".portfolio.local"
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    "users.apps.UsersConfig",  # Must be first
    "django.contrib.contenttypes",  # Required by auth
    "django.contrib.auth",  # Required for user model
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "corsheaders",
    "axes",  # Django Axes for admin login brute force protection
    # Local apps
    "astrophotography.apps.AstrophotographyConfig",
    "programming.apps.ProgrammingConfig",
    "inbox.apps.InboxConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Must be before CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "inbox.middleware.ContactFormKillSwitchMiddleware",
    # Check kill switch early (after security, before sessions)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",  # Axes middleware must be after AuthenticationMiddleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": env.str("DB_ENGINE", default=cast(Any, "django.db.backends.postgresql")),
        "NAME": env.str("DB_NAME", default=cast(Any, "portfolio")),
        "USER": env.str("DB_USER", default=cast(Any, "postgres")),
        "PASSWORD": env.str("DB_PASSWORD", default=cast(Any, "postgres")),
        "HOST": env.str("DB_HOST", default=cast(Any, "db")),
        "PORT": env.int("DB_PORT", default=cast(Any, 5432)),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Cache Configuration (for rate limiting and throttling)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 3600,  # 1 hour default timeout
        "OPTIONS": {"MAX_ENTRIES": 10000},
    }
}

# File Upload Settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "contact": "5/hour",  # Contact form - more restrictive
        "api": "200/hour",  # General API calls
    },
}

# Django Axes Configuration (Admin Login Protection)
AXES_FAILURE_LIMIT = 5  # Number of failed login attempts before lockout
AXES_COOLOFF_TIME = 1  # Hours to lockout after limit exceeded
AXES_RESET_ON_SUCCESS = True  # Reset failure count on successful login
AXES_ENABLE_ADMIN = True  # Enable Axes admin interface
AXES_VERBOSE = True  # Enable verbose logging
# Axes configuration - works directly with email since USERNAME_FIELD = 'email'
AXES_USERNAME_FORM_FIELD = "username"  # Django admin form uses 'username' field name but value is email (USERNAME_FIELD = 'email')

# Authentication backends with axes protection
# Axes backend must be first to intercept login attempts
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # Axes backend (must be first)
    "django.contrib.auth.backends.ModelBackend",
]

# Email Configuration
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND",
    default=cast(Any, "django.core.mail.backends.smtp.EmailBackend"),
)
EMAIL_HOST = env.str("EMAIL_HOST", default=cast(Any, "smtp.gmail.com"))
EMAIL_PORT = env.int("EMAIL_PORT", default=cast(Any, 587))
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=cast(Any, True))
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default=cast(Any, ""))
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default=cast(Any, ""))
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")
CONTACT_EMAIL = env.str("CONTACT_EMAIL")

# Import local settings if available (for local development)
try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
