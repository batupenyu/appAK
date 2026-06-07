@echo off
title Build AppAK Desktop
cd /d "D:\App\AppAK_Desk"

echo ========================================
echo   Build AppAK - PyInstaller
echo ========================================
echo.

echo [1/3] Install dependencies ke Python system...
python -m pip install django python-decouple xhtml2pdf pyinstaller --quiet

echo [2/3] Menjalankan PyInstaller...
python -m PyInstaller --clean AppAK.spec

echo.
echo [3/3] Selesai! Hasil build ada di: dist\AppAK\AppAK.exe
echo Distribusikan seluruh folder dist\AppAK\ ke komputer lain.
echo.
pause
