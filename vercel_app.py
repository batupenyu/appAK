"""
Vercel WSGI handler for Django app.
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")

try:
    import django
    from django.core.wsgi import get_wsgi_application
    django.setup()

    # Run migrations on every cold start (required for SQLite in /tmp)
    from django.core.management import call_command
    call_command("migrate", "--run-syncdb", verbosity=0)

    application = get_wsgi_application()
except Exception:
    import traceback
    traceback.print_exc()

    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/html; charset=utf-8')])
        return [b"<h1>Django Initialization Error</h1><p>Check Vercel logs.</p>"]
