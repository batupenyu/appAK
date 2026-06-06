"""
Vercel WSGI handler for Django app.
"""
import os
import sys
import traceback

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")

def _error_application(environ, start_response):
    status = '500 Internal Server Error'
    response_headers = [('Content-Type', 'text/html; charset=utf-8')]
    start_response(status, response_headers)
    error_html = b"<html><body><h1>Django Initialization Error</h1><p>Check Vercel logs.</p></body></html>"
    return [error_html]

application = _error_application
try:
    import django
    from django.core.wsgi import get_wsgi_application
    django.setup()
    application = get_wsgi_application()
except Exception:
    pass
