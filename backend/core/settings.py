# backend/core/settings.py
import os
from pathlib import Path
from typing import Any, cast

import environ

from django.utils.translation import gettext_lazy as _

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

# Security Hardening
# https://docs.djangoproject.com/en/5.2/ref/settings/#security
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_BROWSER_XSS_FILTER = env.bool("SECURE_BROWSER_XSS_FILTER", default=True)

# Domain settings
ADMIN_DOMAIN = env.str("ADMIN_DOMAIN", default="admin.portfolio.local")
API_DOMAIN = env.str("API_DOMAIN", default="api.portfolio.local")

# Filter out empty values to prevent "https://" or empty host entries
_base_hosts = [ADMIN_DOMAIN, API_DOMAIN]
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[]) + [h for h in _base_hosts if h]

if DEBUG:
    ALLOWED_HOSTS += [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
if ADMIN_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{ADMIN_DOMAIN}")
if API_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{API_DOMAIN}")

if DEBUG:
    if API_DOMAIN:
        CORS_ALLOWED_ORIGINS.append(f"http://{API_DOMAIN}")
        CORS_ALLOWED_ORIGINS.append(f"http://{API_DOMAIN}:3000")

CORS_ALLOW_CREDENTIALS = True

# Custom user model - this needs to be set before INSTALLED_APPS
AUTH_USER_MODEL = "users.User"

# CSRF Settings
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if ADMIN_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{ADMIN_DOMAIN}")
if API_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{API_DOMAIN}")

CSRF_COOKIE_DOMAIN = env.str("CSRF_COOKIE_DOMAIN", default=None)
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
    "django.contrib.postgres",
    # Third party apps
    "rest_framework",
    "corsheaders",
    "axes",  # Django Axes for admin login brute force protection
    # Local apps
    "astrophotography.apps.AstrophotographyConfig",
    "programming.apps.ProgrammingConfig",
    "inbox.apps.InboxConfig",
    "taggit",
    "django_countries",
    "django_select2",
    "django_ckeditor_5",
    "core",
]

# Security Settings (for Nginx SSL termination)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",  # Must be near the top
    "corsheaders.middleware.CorsMiddleware",  # Must be before CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "inbox.middleware.ContactFormKillSwitchMiddleware",
    # Check kill switch early (after security, before sessions)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Enable language selection
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
        "PORT": (
            env.int("DB_PORT", default=cast(Any, 5432))
            if env.str("DB_PORT", default="5432")
            else 5432
        ),
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

# Supported languages

LANGUAGES = [
    ("en", _("English")),
    ("pl", _("Polish")),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "core", "locale"),
    os.path.join(BASE_DIR, "astrophotography", "locale"),
]

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

# Cache Configuration (Redist for production-grade caching)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL", default="redis://redis:6379/1"),
        "TIMEOUT": 3600,
    },
    "select2": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL", default="redis://redis:6379/2"),
        "TIMEOUT": 3600,
    },
}

# Django Select2 Configuration
SELECT2_CACHE_BACKEND = "select2"
# Disable i18n file loading for English (default locale) to prevent TypeError
# when i18n file loads before Select2 itself
SELECT2_I18N = "none"

# File Upload Settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO" if not DEBUG else "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple" if not DEBUG else "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "core": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
    },
}

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
        "gallery": "2000/hour",  # Gallery views - relaxed for browsing
    },
}

# Django Axes Configuration (Admin Login Protection)
AXES_FAILURE_LIMIT = 5  # Number of failed login attempts before lockout
AXES_COOLOFF_TIME = 1  # Hours to lockout after limit exceeded
AXES_RESET_ON_SUCCESS = True  # Reset failure count on successful login
AXES_ENABLE_ADMIN = True  # Enable Axes admin interface
AXES_VERBOSE = True  # Enable verbose logging
# Axes configuration - works directly with email since USERNAME_FIELD = 'email'
AXES_USERNAME_FORM_FIELD = "username"  # Value is email (USERNAME_FIELD = 'email')

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
# Handle empty string from docker-compose
_port_str = env.str("EMAIL_PORT", default="587")
EMAIL_PORT = int(_port_str) if _port_str and _port_str.strip() else 587
_tls_str = env.str("EMAIL_USE_TLS", default="True")
EMAIL_USE_TLS = _tls_str.lower() == "true" if _tls_str else True
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default=cast(Any, ""))
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default=cast(Any, ""))
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="noreply@example.com")
CONTACT_EMAIL = env.str("CONTACT_EMAIL", default="admin@example.com")

# CKEditor 5 Configuration
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "link",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "imageUpload",
        ],
    },
    "extends": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
        ],
        "toolbar": [
            "heading",
            "|",
            "outdent",
            "indent",
            "|",
            "bold",
            "italic",
            "link",
            "underline",
            "strikethrough",
            "code",
            "|",
            "codeBlock",
            "sourceEditing",
            "insertImage",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "blockQuote",
            "imageUpload",
            "|",
            "fontSize",
            "fontFamily",
            "fontColor",
            "fontBackgroundColor",
            "mediaEmbed",
            "removeFormat",
            "insertTable",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "|",
                "imageStyle:alignLeft",
                "imageStyle:alignCenter",
                "imageStyle:alignRight",
            ],
            "styles": ["alignLeft", "alignCenter", "alignRight"],
        },
    },
}

CKEDITOR_5_CUSTOM_CSS = "css/ckeditor_admin_fix.css"
