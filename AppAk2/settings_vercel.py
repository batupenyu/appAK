"""
Settings for Vercel deployment.
Extends the main settings but with Vercel-specific configurations.
"""

from .settings import *
import os

# Override settings for Vercel deployment
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Update ALLOWED_HOSTS for Vercel deployment
ALLOWED_HOSTS = ['*']

# Static files for Vercel
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CSRF settings for Vercel
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://*.now.sh',
]

# Import dj_database_url for parsing DATABASE_URL
import dj_database_url

# Database configuration for Vercel
DB_PASSWORD = os.environ.get('DB_PASSWORD')

if DB_PASSWORD:
    # Supabase direct connection via DB_* env vars (preferred, works on Vercel)
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': DB_PASSWORD,
        'HOST': os.getenv('DB_HOST', 'db.bcltnyhzcmhxdwlemsye.supabase.co'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
elif os.environ.get('DATABASE_URL'):
    # Fallback: parse DATABASE_URL (e.g. Transaction pooler or direct string)
    parsed = dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
    if parsed.get('ENGINE') == 'django.db.backends.postgresql':
        if 'OPTIONS' not in parsed:
            parsed['OPTIONS'] = {}
        parsed['OPTIONS']['sslmode'] = 'require'
    DATABASES['default'] = parsed

# Media files: use Vercel Blob storage if token is available
if os.environ.get('BLOB_READ_WRITE_TOKEN'):
    DEFAULT_FILE_STORAGE = 'AppAk2.storage_backends.VercelBlobStorage'
    MEDIA_URL = f"https://{os.environ.get('BLOB_STORE_ID', '')}.private.blob.vercel-storage.com/"
