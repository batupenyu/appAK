"""
Settings for Vercel deployment.
Extends the main settings but with Vercel-specific configurations.
"""

from .settings import *
import os

# Override settings for Vercel deployment
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Update ALLOWED_HOSTS for Vercel deployment
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.vercel.app',  # Allow all Vercel domains
    '.now.sh',      # Legacy Vercel domain pattern
]

# Static files for Vercel
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CSRF settings for Vercel
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.now.sh',
]

# Database configuration for Vercel
import dj_database_url

if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )