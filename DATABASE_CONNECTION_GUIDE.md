# Panduan Koneksi Database

## Cara Kerja Sistem

Aplikasi ini dirancang dengan sistem fallback otomatis untuk koneksi database:

1. **Prioritas Utama**: Jika kredensial Supabase lengkap dan valid, sistem akan menggunakan PostgreSQL
2. **Fallback**: Jika kredensial Supabase tidak lengkap atau kosong, sistem otomatis menggunakan SQLite

## File Konfigurasi

### .env
- Digunakan untuk menyimpan kredensial database
- Jika semua variabel penting kosong, sistem akan menggunakan SQLite
- Variabel penting: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST

### .env.example
- Template untuk tim pengembang
- Berisi struktur konfigurasi dasar

### .env.production
- Konfigurasi untuk lingkungan produksi
- Termasuk pengaturan SSL untuk koneksi aman

## Variabel Lingkungan

### Database Configuration
| Variabel | Deskripsi | Contoh |
|----------|-----------|---------|
| DB_NAME | Nama database | postgres |
| DB_USER | Username database | postgres |
| DB_PASSWORD | Password database | your_password |
| DB_HOST | Host database | your-project.supabase.co |
| DB_PORT | Port koneksi | 5432 atau 6543 |
| DB_SSL | Aktifkan SSL | true/false |
| DB_SSL_CERT_PATH | Lokasi sertifikat SSL | ./ssl/cert.crt |

### Supabase Client Configuration
| Variabel | Deskripsi | Contoh |
|----------|-----------|---------|
| SUPABASE_URL | URL proyek Supabase | https://your-project.supabase.co |
| SUPABASE_ANON_KEY | Kunci anonim Supabase | your_anon_key |
| SUPABASE_SERVICE_KEY | Kunci layanan Supabase | your_service_key |

### Aplikasi Configuration
| Variabel | Deskripsi | Contoh |
|----------|-----------|---------|
| NODE_ENV | Lingkungan aplikasi | development/production |
| SECRET_KEY/DJANGO_SECRET_KEY | Kunci rahasia Django | your_secret_key |
| DEBUG | Mode debug | True/False |
| ALLOWED_HOSTS | Host yang diizinkan | localhost,127.0.0.1 |

## Pengujian Koneksi

Gunakan skrip `test_connection.py` untuk menguji koneksi database:

```bash
python test_connection.py
```

Skrip ini akan:
- Mencoba membuat koneksi ke database
- Menampilkan jenis database yang digunakan
- Menampilkan informasi koneksi jika menggunakan PostgreSQL

## Troubleshooting

Jika koneksi gagal:
1. Pastikan semua kredensial di .env benar dan lengkap
2. Periksa apakah firewall mengizinkan koneksi ke server database
3. Verifikasi bahwa SSL diaktifkan jika diperlukan oleh server
4. Pastikan nama host, port, dan nama database benar

## Catatan Keamanan

- Jangan pernah commit file .env ke repositori
- Gunakan .env.example sebagai template untuk tim
- Selalu gunakan password yang kuat untuk produksi
- Aktifkan SSL untuk koneksi produksi