"""
Vercel entry point for Django application.

This file serves as an alternative entry point for Vercel deployments.
"""

import os
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppAk2.settings')

# Create the WSGI application
application = get_wsgi_application()