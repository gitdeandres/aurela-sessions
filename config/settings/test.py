from .base import *

# Use a dedicated PostgreSQL test database, isolated from development.
# pytest-django creates and destroys it automatically on each test run.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aurela_test',
        'USER': ENV.str(var='POSTGRES_USER'),
        'PASSWORD': ENV.str(var='POSTGRES_PASSWORD'),
        'HOST': ENV.str(var='POSTGRES_HOST'),
        'PORT': ENV.int(var='POSTGRES_PORT'),
    }
}

# Disable pagination in tests for simpler response assertions
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_PAGINATION_CLASS': None,
    'PAGE_SIZE': None,
}
