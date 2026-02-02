"""
Local development settings for AppAK project.
"""

from .settings import *

# Override settings for local development
DEBUG = True

# Allow all local addresses
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '[::1]',
]

# Static files for local development
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# For local development, we can use the default CSRF setting name
if 'CSRF_TRUSTED_ORIGINS' in locals():
    CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS