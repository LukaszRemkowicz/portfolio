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
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_BROWSER_XSS_FILTER = env.bool("SECURE_BROWSER_XSS_FILTER", default=True)

# Domain settings
SITE_DOMAIN = env.str("SITE_DOMAIN", default="portfolio.local")
ADMIN_DOMAIN = env.str("ADMIN_DOMAIN", default="admin.portfolio.local")
API_DOMAIN = env.str("API_DOMAIN", default="api.portfolio.local")

# Secure Media Settings
# Expiration for signed image URLs in seconds (default: 1 hour)
SECURE_MEDIA_URL_EXPIRATION = env.int("SECURE_MEDIA_URL_EXPIRATION", default=3600)

# Filter out empty values and consolidate hosts
_base_hosts = [SITE_DOMAIN, ADMIN_DOMAIN, API_DOMAIN]
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[]) + [h for h in _base_hosts if h]

if DEBUG:
    ALLOWED_HOSTS += [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]

USE_X_FORWARDED_HOST = True

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = False
# Handle empty string from env to avoid [''] in the list
_cors_env = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOWED_ORIGINS = [o for o in _cors_env if o]

# Automatically add our domains to CORS and CSRF trusted lists
for h in _base_hosts:
    if h:
        CORS_ALLOWED_ORIGINS.append(f"https://{h}")
        if DEBUG:
            CORS_ALLOWED_ORIGINS.append(f"http://{h}")
            CORS_ALLOWED_ORIGINS.append(f"http://{h}:3000")

# Remove duplicates
CORS_ALLOWED_ORIGINS = list(set(CORS_ALLOWED_ORIGINS))
CORS_ALLOW_CREDENTIALS = True

# Custom user model - this needs to be set before INSTALLED_APPS
AUTH_USER_MODEL = "users.User"

# CSRF & Session Settings
# Sharing cookies across subdomains
CSRF_COOKIE_DOMAIN = env.str("CSRF_COOKIE_DOMAIN", default=".portfolio.local")
SESSION_COOKIE_DOMAIN = env.str("SESSION_COOKIE_DOMAIN")

# CSRF Trusted Origins
_csrf_env = env.list("CSRF_TRUSTED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = [o for o in _csrf_env if o]
for h in _base_hosts:
    if h:
        CSRF_TRUSTED_ORIGINS.append(f"https://{h}")
        if DEBUG:
            CSRF_TRUSTED_ORIGINS.append(f"http://{h}")

# Remove duplicates
CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS))

CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    "parler",
    "users.apps.UsersConfig",  # Must be first
    "django.contrib.contenttypes",  # Required by auth
    "django.contrib.auth",  # Required for user model
    "core.admin_config.PortfolioAdminConfig",  # Custom AdminSite replacement
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third party apps
    "rest_framework",
    "corsheaders",
    "axes",  # Django Axes for admin login brute force protection
    "django_extensions",
    # Local apps
    "astrophotography.apps.AstrophotographyConfig",
    "programming.apps.ProgrammingConfig",
    "inbox.apps.InboxConfig",
    "django_countries",
    "django_select2",
    "django_ckeditor_5",
    "core.apps.CoreConfig",
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


# Third Party API Keys
# ==============================================================================
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": env.str("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env.str("DB_NAME", default="portfolio"),
        "USER": env.str("DB_USER", default="postgres"),
        "PASSWORD": env.str("DB_PASSWORD", default="postgres"),
        "HOST": env.str("DB_HOST", default="db"),
        "PORT": env.str("DB_PORT", default="5432"),
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

# --- Language Configuration ---
# Change this ONE variable to switch default language (Order & Protection)
PARLER_DEFAULT_LANGUAGE_CODE = "en"

LANGUAGE_CODE = PARLER_DEFAULT_LANGUAGE_CODE

# Supported languages
LANGUAGES = [
    ("en", _("English")),
    ("pl", _("Polish")),
]

# Dynamically construct PARLER_LANGUAGES based on default
# Ensures the default language depends on PARLER_DEFAULT_LANGUAGE_CODE
# and is always the FIRST tab.
_other_languages = [lang[0] for lang in LANGUAGES if lang[0] != PARLER_DEFAULT_LANGUAGE_CODE]
_parler_languages_list = [{"code": PARLER_DEFAULT_LANGUAGE_CODE}] + [
    {"code": code} for code in _other_languages
]

PARLER_LANGUAGES = {
    None: tuple(_parler_languages_list),
    "default": {
        "fallback": PARLER_DEFAULT_LANGUAGE_CODE,
        "hide_untranslated": False,
    },
}

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

if not DEBUG:
    # We handle SSL Redirect and HSTS in Nginx, so we silence these checks
    SILENCED_SYSTEM_CHECKS = ["security.W004", "security.W008"]

ADMIN_SITE_ORDERING = (
    {
        "app": "astrophotography",
        "label": "Astrophotography",
        "models": (
            "astrophotography.AstroImage",
            "astrophotography.MainPageLocation",
            "astrophotography.MainPageBackgroundImage",
            "astrophotography.MeteorsMainPageConfig",
            "astrophotography.Place",
            "astrophotography.Tag",
        ),
    },
    {
        "app": "astrophotography",
        "label": "Equipment",
        "models": (
            "astrophotography.Camera",
            "astrophotography.Lens",
            "astrophotography.Telescope",
            "astrophotography.Tracker",
            "astrophotography.Tripod",
        ),
    },
    {
        "app": "inbox",
        "label": "Inbox",
        "models": ("inbox.ContactMessage",),
    },
    {
        "app": "users",
        "label": "Users & Access",
        "models": ("users.User", "users.Profile", "auth.Group"),
    },
    {"app": "axes", "label": "Security Logs"},
    {
        "app": "programming",
        "label": "Programming",
        "models": ("programming.Project", "programming.ProjectImage"),
    },
    {
        "app": "core",
        "label": "Core Settings",
        "models": ("core.LandingPageSettings", "core.TranslationTask"),
    },
)

# ===========================
# Celery Configuration
# ===========================

# Redis connection for Celery broker and result backend
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")

# Celery task settings
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Task execution settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Result backend settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
