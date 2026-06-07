# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Kumpulkan semua hidden imports Django
hiddenimports = (
    collect_submodules('django')
    + collect_submodules('pegawai')
    + collect_submodules('AppAk2')
    + [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.template.defaulttags',
        'django.template.defaultfilters',
        'django.template.loader_tags',
        'pkg_resources.py2_warn',
        'decouple',
        'xhtml2pdf',
        'reportlab',
    ]
)

datas = (
    collect_data_files('django')
    + collect_data_files('xhtml2pdf')
    + collect_data_files('reportlab')
    + [
        ('templates', 'templates'),
        ('pegawai/templates', 'pegawai/templates'),
        ('pegawai/static', 'pegawai/static'),
        ('pegawai/migrations', 'pegawai/migrations'),
        ('AppAk2', 'AppAk2'),
        ('pegawai', 'pegawai'),
        ('db.sqlite3', '.'),
        ('mediafiles', 'mediafiles'),
    ]
)

a = Analysis(
    ['desktop_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['psycopg2', 'dj_database_url'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AppAK',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # False untuk sembunyikan cmd window (ganti jika sudah stabil)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AppAK',
)
