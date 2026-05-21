"""
Vercel WSGI handler for Django app.
"""
import os
import sys
import traceback

# ── Setup path ────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)

# ── Initialize Django ────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")

# Default fallback application (in case of errors)
def _error_application(environ, start_response):
    status = '500 Internal Server Error'
    response_headers = [('Content-Type', 'text/html; charset=utf-8')]
    start_response(status, response_headers)
    
    error_html = f"""
    <html>
    <head><title>Django Initialization Error</title></head>
    <body>
    <h1>Django Initialization Error</h1>
    <h2>Environment Variables:</h2>
    <pre>
DB_HOST={os.environ.get('DB_HOST', 'NOT SET')}
DB_NAME={os.environ.get('DB_NAME', 'NOT SET')}
DB_USER={os.environ.get('DB_USER', 'NOT SET')}
DEBUG={os.environ.get('DEBUG', 'NOT SET')}
DJANGO_SETTINGS_MODULE={os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}
    </pre>
    </body>
    </html>
    """.encode('utf-8')
    
    return [error_html]

# Try to initialize Django
application = _error_application
try:
    import django
    from django.core.wsgi import get_wsgi_application
    django.setup()
    application = get_wsgi_application()
except Exception as e:
    # Keep fallback application
    _traceback_str = traceback.format_exc()
    
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, response_headers)
        
        error_html = f"""
        <html>
        <head><title>Django Initialization Error</title></head>
        <body>
        <h1>Django Initialization Error</h1>
        <pre>{_traceback_str}</pre>
        <h2>Environment Variables:</h2>
        <pre>
DB_HOST={os.environ.get('DB_HOST', 'NOT SET')}
DB_NAME={os.environ.get('DB_NAME', 'NOT SET')}
DB_USER={os.environ.get('DB_USER', 'NOT SET')}
DEBUG={os.environ.get('DEBUG', 'NOT SET')}
DJANGO_SETTINGS_MODULE={os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}
        </pre>
        </body>
        </html>
        """.encode('utf-8')
        
        return [error_html]