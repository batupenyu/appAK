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
logger.setLevel(logging.INFO)

# ── 1. Project root on sys.path ────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))          # e.g. D:\App\AppAK
sys.path.insert(0, _here)
logger.info("App root: %r", _here)

# ── 2. Django settings module — matches manage.py ──────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")
logger.info("DJANGO_SETTINGS_MODULE=%s", os.environ["DJANGO_SETTINGS_MODULE"])

# ── 3. Boilerplate WSGI initialisation ─────────────────────────────
from django.core.wsgi import get_wsgi_application  # noqa: E402
try:
    application = get_wsgi_application()
except Exception:
    logger.critical("Django WSGI initialisation failed", exc_info=True)
    raise
