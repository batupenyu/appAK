# Aplikasi Ak (AppAK)

Aplikasi ini telah dikonfigurasi untuk menggunakan Supabase sebagai database, dengan kemampuan fallback ke SQLite saat kredensial Supabase belum disediakan.

## Status Saat Ini

- Database: Menggunakan SQLite (karena kredensial Supabase belum diisi)
- Mode: Development
- Pesan: "Supabase credentials not found or incomplete. Using SQLite for now."

## Konfigurasi Supabase

Untuk beralih ke Supabase:

1. Dapatkan kredensial dari dashboard Supabase Anda
2. Isi file `.env` dengan kredensial yang benar:
   ```
   DB_NAME=nama_database_anda
   DB_USER=username_supabase
   DB_PASSWORD=password_supabase
   DB_HOST=project-id.supabase.co
   ```
3. Jalankan migrasi ulang:
   ```bash
   python manage.py migrate
   ```

## Perintah-perintah Penting

- Jalankan aplikasi: `python manage.py runserver`
- Lakukan migrasi: `python manage.py migrate`
- Gunakan SQLite eksplisit: `python manage.py migrate --settings=AppAk2.settings_sqlite`
- Gunakan Supabase (setelah konfigurasi): `python manage.py migrate`

## Struktur File Penting

- `AppAk2/settings.py` - Konfigurasi utama dengan logika fallback
- `AppAk2/settings_sqlite.py` - Konfigurasi alternatif untuk SQLite
- `.env` - Tempat menyimpan kredensial (jangan commit ke repo!)
- `.env.example` - Template untuk kredensial
- `SUPABASE_SETUP.md` - Dokumentasi konfigurasi Supabase

## Catatan

Sistem dirancang untuk tetap berfungsi meskipun kredensial Supabase belum disiapkan. Ini memungkinkan pengembangan berkelanjutan tanpa harus langsung terkoneksi ke Supabase.