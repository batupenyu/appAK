"""
Database Connection Test Script
This script tests the database connection using Django's configuration
"""
import os
import sys
import django
from django.conf import settings
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppAk2.settings')
django.setup()

def test_db_connection():
    try:
        # Establish database connection
        cursor = connection.cursor()

        # Simple query to test connection
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        if result:
            print("[SUCCESS] Database connection successful!")

            # Determine which database is being used
            engine = settings.DATABASES['default']['ENGINE']
            if 'sqlite' in engine:
                print("[INFO] Using: SQLite (fallback)")
            elif 'postgresql' in engine:
                print("[INFO] Using: PostgreSQL (Supabase)")

                # Show connection details (without sensitive info)
                host = settings.DATABASES['default'].get('HOST', 'Not specified')
                port = settings.DATABASES['default'].get('PORT', 'Not specified')
                name = settings.DATABASES['default'].get('NAME', 'Not specified')
                print(f"[INFO] Connected to: {host}:{port}/{name}")
            else:
                print(f"[INFO] Using: {engine}")

            return True
        else:
            print("[ERROR] Database connection failed - query didn't return expected result")
            return False

    except Exception as e:
        print(f"[ERROR] Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("[INFO] Testing database connection...")
    success = test_db_connection()

    if success:
        print("\n[SUCCESS] Connection test completed successfully!")
    else:
        print("\n[ERROR] Connection test failed!")
        sys.exit(1)