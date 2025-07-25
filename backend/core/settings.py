"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
from typing import Any, cast
import environ
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)
# reading .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default=cast(Any, 'django-insecure-development-key'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=cast(Any, 'True'))

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://portfolio.local',
    'http://portfolio.local',
    'http://portfolio.local:3000',
]
CORS_ALLOW_CREDENTIALS = True

# Domain settings
ADMIN_DOMAIN = 'admin.portfolio.local'
API_DOMAIN = 'portfolio.local'

ALLOWED_HOSTS = [ADMIN_DOMAIN, API_DOMAIN, 'localhost', '127.0.0.1', '0.0.0.0', '172.10.0.3', 'backend']

# Custom user model - this needs to be set before INSTALLED_APPS
AUTH_USER_MODEL = 'users.User'

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [f'https://{ADMIN_DOMAIN}', f'https://{API_DOMAIN}']
CSRF_COOKIE_DOMAIN = '.portfolio.local'
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    'users.apps.UsersConfig',  # Must be first
    'django.contrib.contenttypes',  # Required by auth
    'django.contrib.auth',  # Required for user model
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'astrophotography.apps.AstrophotographyConfig',
    'programming.apps.ProgrammingConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be before CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env.str('DB_ENGINE', default=cast(Any, 'django.db.backends.postgresql')),
        'NAME': env.str('DB_NAME', default=cast(Any, 'portfolio')),
        'USER': env.str('DB_USER', default=cast(Any, 'postgres')),
        'PASSWORD': env.str('DB_PASSWORD', default=cast(Any, 'postgres')),
        'HOST': env.str('DB_HOST', default=cast(Any, 'db')),
        'PORT': env.int('DB_PORT', default=cast(Any, 5432)),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File Upload Settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rest Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
