import os
from pathlib import Path

import environ

# Project root directory (three levels up from this file: settings/ → config/ → root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
ENV_FILEPATH = os.path.join(BASE_DIR, '.env')
ENV = environ.Env()
environ.Env.read_env(env_file=ENV_FILEPATH)

# Core Django configuration
SETTINGS_MODULE = ENV.str(var='SETTINGS_MODULE')
SECRET_KEY = ENV.str(var='SECRET_KEY')
ALLOWED_HOSTS = ENV.list(var='ALLOWED_HOSTS', default=[])

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

# URLs and application entry points
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': ENV.str(var='POSTGRES_DB'),
        'USER': ENV.str(var='POSTGRES_USER'),
        'PASSWORD': ENV.str(var='POSTGRES_PASSWORD'),
        'HOST': ENV.str(var='POSTGRES_HOST'),
        'PORT': ENV.int(var='POSTGRES_PORT'),
    }
}

# REST Framework
# AllowAny: authentication is explicitly out of scope for this challenge
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'sessions_app.exceptions.custom_exception_handler',
}

# Internationalisation
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'

# Default primary key type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
