import os
import sys
import time
import threading
import webbrowser
from wsgiref.simple_server import make_server, WSGIRequestHandler


# Arahkan BASE_DIR ke folder tempat .exe atau script berada
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8000
URL = f"http://127.0.0.1:{PORT}/pegawai/"


class SilentHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress request logs


def setup_django():
    sys.path.insert(0, BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")

    import django
    from django.conf import settings

    # Setup Django terlebih dahulu agar settings ter-load
    if not settings.configured:
        django.setup()

    # Patch path ke lokasi .exe (override nilai dari settings.py)
    db_path = os.path.join(BASE_DIR, "db.sqlite3")
    settings.DATABASES["default"]["NAME"] = db_path
    settings.MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")
    settings.STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

    # Nonaktifkan FK check di file db yang sebenarnya dipakai
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
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open(URL)), daemon=True).start()
    run_server()
