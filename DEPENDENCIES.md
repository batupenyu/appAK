# Dependensi Proyek

## Paket Python yang Digunakan

### Utama
- **Django** (versi >=4.2.0): Framework web utama
- **psycopg2-binary** (versi >=2.9.0): Driver PostgreSQL untuk Python
- **python-decouple** (versi >=3.8): Untuk membaca variabel lingkungan dari file .env
- **python-dotenv** (versi >=1.0.0): Alternatif untuk manajemen variabel lingkungan

## Instalasi

Untuk menginstal semua dependensi, gunakan perintah:

```bash
pip install -r requirements.txt
```

## Catatan

- `psycopg2-binary` digunakan untuk koneksi ke database PostgreSQL/Supabase
- `python-decouple` dan `python-dotenv` keduanya menyediakan fungsionalitas serupa untuk membaca file .env
- Proyek ini menggunakan `python-decouple` dalam konfigurasi settings.py saat ini
- Kedua paket tersebut kompatibel dan dapat digunakan bersamaan jika diperlukan