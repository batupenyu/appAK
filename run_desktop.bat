@echo off
title AppAK - Angka Kredit Pegawai
cd /d "D:\App\AppAK_Desk"

echo ========================================
echo   AppAK - Angka Kredit Pegawai
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    set PYTHON=D:\App\AppAK_Desk\.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

%PYTHON% manage.py migrate --run-syncdb 2>nul

%PYTHON% desktop_launcher.py

pause
