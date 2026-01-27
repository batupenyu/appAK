@echo off
REM Script untuk menjalankan migrasi dengan SQLite sementara
echo Setting up with SQLite temporarily...
python manage.py migrate --settings=AppAk2.settings_sqlite
echo Migration with SQLite completed!

pause