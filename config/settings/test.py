from .base import *

# Use in-memory SQLite for tests: faster, no external dependencies,
# and isolated from the development database.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable pagination in tests for simpler response assertions
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_PAGINATION_CLASS': None,
    'PAGE_SIZE': None,
}
