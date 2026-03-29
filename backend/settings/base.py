# backend/core/settings.py
import os
from pathlib import Path
from typing import Any, cast

import environ
import sentry_sdk
from celery.schedules import crontab
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from django.utils.translation import gettext_lazy as _

from common.utils.image import ImageSpec
from users.types import CropperFieldConfig, CropperPreviewShape

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
# reading .env file (optional for local development with Doppler)
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# Project root (repository root where docker-compose.yml lives) for Docker Compose access
PROJECT_ROOT = env.str("PROJECT_ROOT", default=str(BASE_DIR.parent))

# Project Owner
PROJECT_OWNER = env.str("PROJECT_OWNER")

# Sentry Configuration
SENTRY_DSN = env("SENTRY_DSN", default="")
ENABLE_SENTRY = env.bool("ENABLE_SENTRY", default=True)
ENVIRONMENT = env("ENVIRONMENT", default="development")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=cast(Any, False))

if SENTRY_DSN and ENABLE_SENTRY:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        # If you wish to associate users to errors (recommended)
        send_default_pii=DEBUG,
        environment=ENVIRONMENT,
    )

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default=cast(Any, "django-insecure-development-key"))


# Security Hardening
# https://docs.djangoproject.com/en/5.2/ref/settings/#security
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)

SECURE_HSTS_SECONDS = env.bool("SECURE_HSTS_SECONDS", default=31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=not DEBUG)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=not DEBUG)
# These headers are set by Nginx — disable Django's duplicates where possible
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
# X_FRAME_OPTIONS must stay — XFrameOptionsMiddleware crashes if set to None
X_FRAME_OPTIONS = "DENY"


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
# Unconditionally allow local access for container health checks
ALLOWED_HOSTS += ["localhost", "127.0.0.1", "0.0.0.0"]


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
    "jazzmin",
    "parler",
    "users.apps.UsersConfig",  # Must be first
    "django.contrib.contenttypes",  # Required by auth
    "django.contrib.auth",  # Required for user model
    "core.admin_config.PortfolioAdminConfig",  # Custom AdminSite replacement
    "core.apps.CoreConfig",  # Must be loaded before other Django apps for template overrides
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.sitemaps",
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
    "translation.apps.TranslationConfig",
    "monitoring.apps.MonitoringConfig",
]

# django-extensions shell_plus should default to IPython so interactive
# sessions have proper readline/history behavior instead of plain
# InteractiveConsole fallback.
SHELL_PLUS = "ipython"

# Security Settings (for Nginx SSL termination)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",  # Must be near the top
    "corsheaders.middleware.CorsMiddleware",  # Must be before CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "common.middleware.RequestCorrelationMiddleware",
    "inbox.middleware.ContactFormKillSwitchMiddleware",
    # Check kill switch early (after security, before sessions)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Enable language selection
    "common.middleware.QueryParameterLocaleMiddleware",  # Override with ?lang=
    "django.middleware.common.CommonMiddleware",
    "django.middleware.http.ConditionalGetMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",  # Axes middleware must be after AuthenticationMiddleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "core", "templates")],
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

WSGI_APPLICATION = "settings.wsgi.application"


# Third Party API Keys
# ==============================================================================
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

# LLM Provider Configuration
# Available providers: "gpt", "mock", "gemini", "claude", etc.
# Each service can use a different provider
TRANSLATION_LLM_PROVIDER = env.str("TRANSLATION_LLM_PROVIDER", default="gpt")
MONITORING_LLM_PROVIDER = env.str("MONITORING_LLM_PROVIDER", default="gpt")
RUN_LEGACY_DAILY_TASK = env.bool("RUN_LEGACY_DAILY_TASK", default=False)
DOCKER_LOGS_DIR = env.str("DOCKER_LOGS_DIR", default="/app/docker-logs")
SSR_CACHE_INVALIDATION_URL = env.str(
    "SSR_CACHE_INVALIDATION_URL", default="http://fe:8080/internal/cache/invalidate"
)
SSR_CACHE_INVALIDATION_TOKEN = env.str(
    "SSR_CACHE_INVALIDATION_TOKEN", default="dev-ssr-cache-token"
)

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
def get_default_language() -> str:
    """Returns the default language for the application."""
    return "en"


DEFAULT_APP_LANGUAGE = get_default_language()

# Change this ONE variable to switch default language (Order & Protection)
PARLER_DEFAULT_LANGUAGE_CODE = DEFAULT_APP_LANGUAGE
LANGUAGE_CODE = DEFAULT_APP_LANGUAGE

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

TIME_ZONE = "Europe/Warsaw"

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
_redis_pwd = env.str("REDIS_PASSWORD", default="")
_redis_auth = f":{_redis_pwd}@" if _redis_pwd else ""

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL", default=f"redis://{_redis_auth}redis:6379/1"),
        "TIMEOUT": 3600,
    },
    "select2": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL", default=f"redis://{_redis_auth}redis:6379/2"),
        "TIMEOUT": 3600,
    },
}

# 30 days is effectively infinite for this portfolio
INFINITE_CACHE_TIMEOUT = 3600 * 24 * 30

# Django Select2 Configuration
SELECT2_CACHE_BACKEND = "select2"
# Disable i18n file loading for English (default locale) to prevent TypeError
# when i18n file loads before Select2 itself
SELECT2_I18N = "none"

# File Upload Settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Image Optimization Settings
IMAGE_OPTIMIZATION_SPECS = {
    "AVATAR": ImageSpec(dimension=280, quality=10),
    "PORTRAIT": ImageSpec(dimension=800, quality=35),
    "LANDSCAPE": ImageSpec(dimension=1920, quality=90),
    "THUMBNAIL": ImageSpec(dimension=560, quality=100),
    "DEFAULT": ImageSpec(dimension=1200, quality=75),
}

# TODO: add it somewhere else
USER_ADMIN_CROPPER_FIELD_CONFIGS = (
    CropperFieldConfig(
        field_name="avatar",
        label=_("Avatar"),
        input_id="id_avatar",
        preview_shape=CropperPreviewShape.CIRCLE,
        spec_method="get_avatar_spec",
        crop_aspect_ratio=1.0,
    ),
    CropperFieldConfig(
        field_name="about_me_image",
        label=_("About me image"),
        input_id="id_about_me_image",
        preview_shape=CropperPreviewShape.ROUNDED_SQUARE,
        spec_method="get_portrait_spec",
        crop_aspect_ratio=1.0,
    ),
    CropperFieldConfig(
        field_name="about_me_image2",
        label=_("About me image 2"),
        input_id="id_about_me_image2",
        preview_shape=CropperPreviewShape.ROUNDED_SQUARE,
        spec_method="get_portrait_spec",
        crop_aspect_ratio=1.0,
    ),
)

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

if DEBUG:
    # Disable throttling (or make it very high) in DEBUG mode
    # This prevents development/testing from hitting rate limits
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "10000/hour",
        "user": "100000/hour",
        "contact": "1000/hour",
        "api": "10000/hour",
        "gallery": "100000/hour",
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
        "language": "en",
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
        "language": "en",
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
                "imageStyle:inline",
                "imageStyle:block",
                "imageStyle:side",
            ],
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
        "label": _("Astrophotography"),
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
        "label": _("Equipment"),
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
        "label": _("Inbox"),
        "models": ("inbox.ContactMessage",),
    },
    {
        "app": "users",
        "label": _("Users & Access"),
        "models": ("users.User", "users.Profile", "auth.Group"),
    },
    {"app": "axes", "label": _("Security Logs")},
    {
        "app": "programming",
        "label": _("Programming"),
        "models": ("programming.Project", "programming.ProjectImage"),
    },
    {
        "app": "core",
        "label": _("Core Settings"),
        "models": ("core.LandingPageSettings",),
    },
    {
        "app": "translation",
        "label": _("Translations"),
        "models": ("translation.TranslationTask",),
    },
    {
        "app": "monitoring",
        "label": "Monitoring",
        "models": ("monitoring.LogAnalysis", "monitoring.SitemapAnalysis"),
    },
)

# ===========================
# Celery Beat (Periodic Tasks)
# ===========================


CELERY_BEAT_SCHEDULE = {
    "weekly-log-cleanup": {
        "task": "monitoring.tasks.cleanup_old_logs_task",
        "schedule": crontab(hour=8, minute=0, day_of_week=0),  # 8:00 AM UTC every Sunday
        "kwargs": {
            "days_to_keep": 30,  # Keep last 30 days
        },
        "options": {
            "expires": 1800,  # Task expires after 30 minutes
        },
    },
}

DAILY_MONITORING_LOG_TASK_NAME = (
    "monitoring.tasks.daily_log_analysis_task"
    if RUN_LEGACY_DAILY_TASK
    else "monitoring.tasks.daily_monitoring_agent_log_task"
)

CELERY_BEAT_SCHEDULE["daily-log-analysis"] = {
    "task": DAILY_MONITORING_LOG_TASK_NAME,
    "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC daily
    "options": {
        "expires": 3600,  # Task expires after 1 hour
    },
}

CELERY_BEAT_SCHEDULE["sitemap-analysis"] = {
    "task": "monitoring.tasks.daily_sitemap_analysis_task",
    "schedule": crontab(hour=3, minute=0, day_of_month="1-31/5"),
    "options": {
        "expires": 3600,
    },
}

# ===========================
# Celery Configuration
# ===========================

# Redis connection for Celery broker and result backend
_celery_redis_auth = f":{_redis_pwd}@" if _redis_pwd else ""
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=f"redis://{_celery_redis_auth}redis:6379/0")
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND", default=f"redis://{_celery_redis_auth}redis:6379/0"
)

# Celery task settings
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Task Routing
# Route monitoring tasks to a specific queue so they can be picked up
# ONLY by the host-based worker (which has access to docker CLI)
CELERY_TASK_ROUTES = {
    "monitoring.tasks.daily_log_analysis_task": {"queue": "monitoring"},
    "monitoring.tasks.daily_monitoring_agent_log_task": {"queue": "monitoring"},
    "monitoring.tasks.daily_sitemap_analysis_task": {"queue": "monitoring"},
    "monitoring.tasks.cleanup_old_logs_task": {"queue": "monitoring"},
}

# Task execution settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Result backend settings
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000


# ===========================
# Jazzmin Admin UI Configuration
# ===========================

JAZZMIN_SETTINGS = {
    "site_title": "Portfolio Admin",
    "site_header": "Portfolio",
    "site_brand": "Portfolio Admin",
    "welcome_sign": "Welcome to the Portfolio Admin Interface",
    "copyright": PROJECT_OWNER,
    # User Menu
    "user_avatar": "get_avatar_url",
    # Top Menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "users.User"},
    ],
    # Links on the side menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    # Custom Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user",
        "users.Profile": "fas fa-id-badge",
        "astrophotography.AstroImage": "fas fa-image",
        "astrophotography.MainPageLocation": "fas fa-map-marker-alt",
        "astrophotography.MainPageBackgroundImage": "fas fa-camera",
        "astrophotography.MeteorsMainPageConfig": "fas fa-meteor",
        "astrophotography.Place": "fas fa-globe",
        "astrophotography.Tag": "fas fa-tags",
        "astrophotography.Camera": "fas fa-camera-retro",
        "astrophotography.Lens": "fas fa-search",
        "astrophotography.Telescope": "fas fa-binoculars",
        "astrophotography.Tracker": "fas fa-crosshairs",
        "astrophotography.Tripod": "fas fa-arrows-alt",
        "inbox.ContactMessage": "fas fa-envelope",
        "programming.Project": "fas fa-code",
        "programming.ProjectImage": "fas fa-images",
        "axes.AccessAttempt": "fas fa-user-lock",
        "axes.AccessLog": "fas fa-list-alt",
        "core.LandingPageSettings": "fas fa-sliders-h",
        "translation.TranslationTask": "fas fa-language",
        "monitoring.LogAnalysis": "fas fa-chart-line",
        "monitoring.SitemapAnalysis": "fas fa-sitemap",
    },
    # Changing the order
    "order_with_respect_to": [
        "astrophotography",
        "inbox",
        "users",
        "auth",
        "axes",
        "programming",
        "core",
        "translation",
        "monitoring",
    ],
    "custom_css": "core/css/admin_sidebar.css",
    "show_theme_chooser": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "default_theme_mode": "auto",
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-outline-success",
    },
}
