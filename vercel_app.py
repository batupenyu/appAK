"""
Vercel entry point for Django application.
This file serves as the entry point for Vercel deployments.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module for Vercel deployment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppAk2.settings_vercel')

# Create the WSGI application
app = get_wsgi_application()

# Export the application for Vercel
application = app