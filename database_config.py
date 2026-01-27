import os
import sys
from pathlib import Path

# Menentukan apakah akan menggunakan SQLite atau PostgreSQL
USE_SQLITE_FOR_MIGRATION = os.environ.get('USE_SQLITE_FOR_MIGRATION', 'false').lower() == 'true'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

if USE_SQLITE_FOR_MIGRATION:
    # Gunakan SQLite untuk migrasi
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Gunakan PostgreSQL (Supabase) 
    from decouple import config
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

print(f"Database configuration: {'SQLite' if USE_SQLITE_FOR_MIGRATION else 'PostgreSQL (Supabase)'}")