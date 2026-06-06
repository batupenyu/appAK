"""
Vercel WSGI handler for Django app.
"""

import os
import sys
import traceback  # WAJIB DITAMBAHKAN AGAR TIDAK NAMEERROR

# 1. PAKSA VERCEL MEMBACA PATH INSTALASI MODUL LOKAL
sys.path.append(os.path.join(os.path.dirname(__file__), '.vercel', 'path0', 'extmod'))
sys.path.append(os.path.dirname(__file__))

# 2. SETTING DEFAULT ENVIRONMENT VARIABLES
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AppAk2.settings')

# 3. PROSES INSIALISASI DJANGO
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    app = application
except ModuleNotFoundError as e:
    # Fungsi _error_application Anda berada di sini sebagai fallback
    def _error_application(environ, start_response):
        # ... isi kode fungsi error html Anda ...
        return [error_html]
    app = _error_application


# import os
# import sys
# import traceback

# _here = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, _here)

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")

# def _error_application(environ, start_response):
#     status = '500 Internal Server Error'
#     response_headers = [('Content-Type', 'text/html; charset=utf-8')]
#     start_response(status, response_headers)
    
#     error_html = f"""
#     <html>
#     <head><title>Django Initialization Error</title></head>
#     <body>
#     <h1>Django Initialization Error</h1>
#     <h2>Environment Variables:</h2>
#     <pre>
# DB_HOST={os.environ.get('DB_HOST', 'NOT SET')}
# DB_NAME={os.environ.get('DB_NAME', 'NOT SET')}
# DB_USER={os.environ.get('DB_USER', 'NOT SET')}
# DEBUG={os.environ.get('DEBUG', 'NOT SET')}
# DJANGO_SETTINGS_MODULE={os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT SET')}
#     </pre>
#     </body>
#     </html>
#     """.encode('utf-8')
    
#     return [error_html]

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