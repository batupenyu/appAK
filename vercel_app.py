"""
Naked Vercel entry point — minimalist and self-contained.

Who it works:
1. This file is `vercel_app.py` at the repo root.
2. Vercel adds both the repo root and `/vercel/task/` to sys.path.
3. We add the repo root to sys.path explicitly.
4. We import Django's WSGI application with `AppAk2.settings` as the
   settings module; settings.py reads Vercel's env-var config and
   initialises Postgres over IPv6 via psycopg2.
5. The callable is `application` — the name Vercel delegates to.
"""
import os
import sys
import logging

logger = logging.getLogger("vercel.django")
logger.setLevel(logging.DEBUG)

# ── 1. Project root on sys.path ────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
logger.info("App root: %r", _here)

# ── 2. Django settings module — matches manage.py ──────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")
logger.info("DJANGO_SETTINGS_MODULE=%s", os.environ["DJANGO_SETTINGS_MODULE"])

# Log environment variables (for debugging)
logger.info("DB_HOST=%s", os.environ.get('DB_HOST', 'NOT SET'))
logger.info("DB_NAME=%s", os.environ.get('DB_NAME', 'NOT SET'))
logger.info("DEBUG=%s", os.environ.get('DEBUG', 'NOT SET'))

# ── 3. Boilerplate WSGI initialisation ─────────────────────────────
from django.core.wsgi import get_wsgi_application  # noqa: E402

try:
    logger.info("Attempting to get WSGI application...")
    application = get_wsgi_application()
    logger.info("WSGI application initialized successfully")
except Exception as e:
    logger.critical("Django WSGI initialisation failed: %s", str(e), exc_info=True)
    # Create a fallback error handler
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'Django initialization failed. Check Vercel logs for details.']
