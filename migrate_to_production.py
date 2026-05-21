"""
Script migrasi: SQLite lokal -> PostgreSQL (Supabase) + file -> Vercel Blob

Jalankan dari root project:
    python migrate_to_production.py

Pastikan .env sudah berisi:
    DB_NAME, DB_USER, DB_PASSWORD, DB_HOST  -> Supabase credentials
    BLOB_READ_WRITE_TOKEN                   -> dari Vercel dashboard
    BLOB_STORE_ID                           -> dari Vercel dashboard
"""

import os
import sys
import sqlite3
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AppAk2.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def upload_files_to_blob():
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        print("SKIP upload: BLOB_READ_WRITE_TOKEN tidak ditemukan")
        return

    from vercel.blob import BlobClient
    client = BlobClient()

    media_root = os.path.join(os.path.dirname(__file__), "mediafiles")
    uploaded = 0

    for dirpath, _, filenames in os.walk(media_root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            blob_name = os.path.relpath(filepath, media_root).replace("\\", "/")

            with open(filepath, "rb") as f:
                try:
                    client.put(blob_name, f.read(), access="private", overwrite=True)
                    print(f"  OK {blob_name}")
                    uploaded += 1
                except Exception as e:
                    print(f"  FAIL {blob_name}: {e}")

    print(f"Upload selesai: {uploaded} file")


def migrate_data():
    required = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"SKIP migrasi data: env vars tidak lengkap: {missing}")
        return

    django.setup()

    sqlite_path = os.path.join(os.path.dirname(__file__), "db.sqlite3")
    if not os.path.exists(sqlite_path):
        print("SKIP migrasi data: db.sqlite3 tidak ditemukan")
        return

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    from pegawai.models import Instansi, Pegawai, Penilai, AngkaIntegrasi, AK, AkPendidikan

    tables = [
        ("pegawai_instansi",       Instansi),
        ("pegawai_pegawai",        Pegawai),
        ("pegawai_penilai",        Penilai),
        ("pegawai_angkaintegrasi", AngkaIntegrasi),
        ("pegawai_ak",             AK),
        ("pegawai_akpendidikan",   AkPendidikan),
    ]

    for table_name, Model in tables:
        cur.execute(f"SELECT * FROM {table_name}")
        rows = cur.fetchall()
        if not rows:
            print(f"  - {table_name}: kosong, skip")
            continue

        created = skipped = 0
        for row in rows:
            data = dict(row)
            pk = data.pop("id")
            try:
                _, is_new = Model.objects.update_or_create(pk=pk, defaults=data)
                if is_new:
                    created += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  FAIL {table_name} id={pk}: {e}")

        print(f"  OK {table_name}: {created} baru, {skipped} sudah ada")

    conn.close()
    print("Migrasi data selesai")


if __name__ == "__main__":
    print("=== Upload file ke Vercel Blob ===")
    upload_files_to_blob()
    print()
    print("=== Migrasi data SQLite -> PostgreSQL ===")
    migrate_data()
