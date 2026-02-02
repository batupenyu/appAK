"""
WSGI config for AppAK project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments.
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the Django settings module for local development
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppAk2.settings')

# Create the WSGI application
application = get_wsgi_application()