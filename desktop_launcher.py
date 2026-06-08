import os
import sys
import hmac
import uuid
import time
import hashlib
import threading
import webbrowser
from wsgiref.simple_server import make_server, WSGIRequestHandler

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8000
URL = f"http://127.0.0.1:{PORT}/pegawai/"
HWID_URL = f"http://127.0.0.1:{PORT}/hwid/"
LICENSE_FILE = os.path.join(BASE_DIR, "license.key")
SECRET = b"AppAK-LicenseSecret-2026"


def get_hardware_id():
    mac = uuid.getnode()
    return hashlib.sha256(f"AppAK-{mac}".encode()).hexdigest()[:32].upper()


def is_licensed():
    if not os.path.exists(LICENSE_FILE):
        return False
    try:
        with open(LICENSE_FILE, "r") as f:
            content = f.read().strip()
        hwid, sig = content.split(":")
        expected = hmac.new(SECRET, hwid.encode(), hashlib.sha256).hexdigest().upper()
        return hmac.compare_digest(sig, expected) and hwid == get_hardware_id()
    except Exception:
        return False


class SilentHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


def setup_django():
    sys.path.insert(0, BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")

    import django
    from django.conf import settings

    if not settings.configured:
        django.setup()

    db_path = os.path.join(BASE_DIR, "db.sqlite3")
    settings.DATABASES["default"]["NAME"] = db_path
    settings.MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")
    settings.STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

    import sqlite3 as _sqlite3
    _conn = _sqlite3.connect(db_path)
    _conn.execute("PRAGMA foreign_keys=OFF")
    _conn.commit()
    _conn.close()

    from django.core.management import call_command
    call_command("migrate", "--run-syncdb", verbosity=0)


def run_server():
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    httpd = make_server("127.0.0.1", PORT, application, handler_class=SilentHandler)
    print(f"AppAK berjalan di {URL}")
    httpd.serve_forever()


if __name__ == "__main__":
    setup_django()
    start_url = URL if is_licensed() else HWID_URL
    threading.Thread(
        target=lambda: (time.sleep(1.5), webbrowser.open(start_url)),
        daemon=True
    ).start()
    run_server()
