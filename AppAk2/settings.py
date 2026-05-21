import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Allow Vercel domains and localhost
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'app-ak.vercel.app', '*.vercel.app', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pegawai',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AppAk2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AppAk2.wsgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

try:
    # Load Supabase credentials from environment
    SUPABASE_DB_NAME = config('DB_NAME', default='')
    SUPABASE_DB_USER = config('DB_USER', default='')
    SUPABASE_DB_PASSWORD = config('DB_PASSWORD', default='')
    SUPABASE_DB_HOST = config('DB_HOST', default='')
    USE_SQLITE_FOR_MIGRATION = config('USE_SQLITE_FOR_MIGRATION', default=False, cast=bool)

    # Check if any of the required values are empty
    if (SUPABASE_DB_NAME and SUPABASE_DB_USER and SUPABASE_DB_PASSWORD and SUPABASE_DB_HOST and not USE_SQLITE_FOR_MIGRATION):
        # If all required values exist and are not empty, update to PostgreSQL
        # Use port 5432 for direct connection (not pooler with 6543)
        db_port = 5432 if 'db.' in SUPABASE_DB_HOST else 6543
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': SUPABASE_DB_NAME,
            'USER': SUPABASE_DB_USER,
            'PASSWORD': SUPABASE_DB_PASSWORD,
            'HOST': SUPABASE_DB_HOST,
            'PORT': db_port,
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 10,
                'options': '-c default_transaction_isolation=read_committed',
            },
            'CONN_MAX_AGE': 600,
        }
except Exception as e:
    # If any error occurs, keep SQLite
    pass

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = ['http://localhost:*', 'https://*.vercel.app']
