import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import json
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import base64

# Data pangkat dan golongan
PANGKAT_OPTIONS = {
    "Penata Muda": "III/a",
    "Penata Muda Tingkat I": "III/b",
    "Penata": "III/c",
    "Penata Tingkat I": "III/d",
    "Pembina": "IV/a",
    "Pembina Tingkat I": "IV/b",
    "Pembina Utama Muda": "IV/c",
    "Pembina Utama Madya": "IV/d",
    "Pembina Utama": "IV/e"
}

GOLONGAN_HIERARKI = [
    "III/a", "III/b", "III/c", "III/d",
    "IV/a", "IV/b", "IV/c", "IV/d", "IV/e"
]

# Data jenjang keahlian dan keterampilan
JENJANG_OPTIONS = [
    "KEAHLIAN - AHLI PERTAMA",
    "KEAHLIAN - AHLI MUDA",
    "KEAHLIAN - AHLI MADYA",
    "KEAHLIAN - AHLI UTAMA",
    "KETERAMPILAN - PEMULA",
    "KETERAMPILAN - TERAMPIL",
    "KETERAMPILAN - MAHIR",
    "KETERAMPILAN - PENYELIA"
]

# Data penilaian options
PENILAIAN_OPTIONS = [
    "Sangat Baik",
    "Baik",
    "Butuh Perbaikan",
    "Kurang",
    "Sangat Kurang"
]

# Mapping penilaian to prosentase
PENILAIAN_TO_PROSENTASE = {
    "Sangat Baik": 150,
    "Baik": 100,
    "Butuh Perbaikan": 75,
    "Kurang": 50,
    "Sangat Kurang": 25
}

# Mapping jenjang to koefisien
JENJANG_TO_KOEFISIEN = {
    "KEAHLIAN - AHLI PERTAMA": 12.5,
    "KEAHLIAN - AHLI MUDA": 25,
    "KEAHLIAN - AHLI MADYA": 37.5,
    "KEAHLIAN - AHLI UTAMA": 50,
    "KETERAMPILAN - PEMULA": 3.75,
    "KETERAMPILAN - TERAMPIL": 5,
    "KETERAMPILAN - MAHIR": 12.5,
    "KETERAMPILAN - PENYELIA": 25
}

# Mapping minimal Angka Kredit untuk kenaikan pangkat/jenjang (Versi BKPSDMD)
MINIMAL_AK_MAPPING = {
    # Format: (pangkat_saat_ini, pangkat_tujuan) -> (minimal_pangkat, minimal_jenjang)
    ("III/a", "III/b"): (50, 100),
    ("III/b", "III/c"): (100, 100),
    ("III/c", "III/d"): (100, 200),
    ("III/d", "IV/a"): (200, 200),
    ("IV/a", "IV/b"): (150, 450),
    ("IV/b", "IV/c"): (300, 450),
    ("IV/c", "IV/d"): (450, 450),
    ("IV/d", "IV/e"): (200, None), # Jenjang tidak tersedia (-)
}

# Mapping golongan ke nilai LAMA untuk laporan Penetapan
GOLONGAN_TO_LAMA = {
    "III/a": 0.0,
    "III/b": 50.0,
    "III/c": 0.0,
    "III/d": 100.0,
    # IV/a dst → default 0.0 (tidak perlu ditulis eksplisit)
}

# Fungsi untuk update golongan berdasarkan pangkat
def update_golongan(key):
    st.session_state[f'golongan_{key}'] = PANGKAT_OPTIONS.get(st.session_state.get(f'pangkat_{key}', ''), '')

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem CRUD Pegawai",
    page_icon="👥",
    layout="wide"
)

# Fungsi untuk mendapatkan daftar periode unik dari tabel ak
def get_unique_periods(conn):
    """Mengambil semua pasangan periode tanggal_awal dan tanggal_akhir unik dari ak."""
    cur = conn.cursor()
    # Mengambil pasangan tanggal_awal dan tanggal_akhir yang unik
    # Menggunakan ORDER BY DESC agar periode terbaru muncul di atas
    cur.execute("SELECT DISTINCT tanggal_awal_penilaian, tanggal_akhir_penilaian FROM ak ORDER BY tanggal_awal_penilaian DESC")
    periods = cur.fetchall()
    # Format periode menjadi string untuk selectbox
    formatted_periods = []
    for start_date, end_date in periods:
        # Konversi format YYYY-MM-DD menjadi DD-MM-YYYY untuk tampilan user
        start_display = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        end_display = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        # Format gabungan YYYY-MM-DD digunakan sebagai value di selectbox
        # dan format tampilan DD-MM-YYYY untuk label
        formatted_periods.append(
            (f"{start_display} s/d {end_display}", f"{start_date} s/d {end_date}")
        )
    return formatted_periods

# Judul aplikasi
st.title("📊 Sistem Angka Kredit Pegawai")
st.markdown("---")

# Inisialisasi database
def init_db():
    conn = sqlite3.connect('pegawai.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pegawai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nip TEXT UNIQUE,
            no_seri_karpeg TEXT,
            tempat_lahir TEXT,
            tanggal_lahir DATE,
            jenis_kelamin TEXT,
            pangkat TEXT,
            golongan TEXT,
            tmt_pangkat DATE,
            jabatan TEXT,
            tmt_jabatan DATE,
            unit_kerja TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS instansi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_instansi TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS penilai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            nip TEXT UNIQUE,
            no_seri_karpeg TEXT,
            tempat_lahir TEXT,
            tanggal_lahir DATE,
            jenis_kelamin TEXT,
            pangkat TEXT,
            golongan TEXT,
            tmt_pangkat DATE,
            jabatan TEXT,
            tmt_jabatan DATE,
            unit_kerja TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS angka_integrasi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pegawai_id INTEGER NOT NULL,
            jumlah_angka_integrasi REAL NOT NULL,
            FOREIGN KEY (pegawai_id) REFERENCES pegawai (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ak (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pegawai_id INTEGER,
            instansi_id INTEGER,
            penilai_id INTEGER,
            tanggal_awal_penilaian DATE,
            tanggal_akhir_penilaian DATE,
            penilaian TEXT,
            prosentase INTEGER,
            koefisien REAL,
            jumlah_angka_kredit REAL,
            tanggal_ditetapkan DATE,
            tempat_ditetapkan TEXT,
            jenjang TEXT,
            FOREIGN KEY (pegawai_id) REFERENCES pegawai (id),
            FOREIGN KEY (instansi_id) REFERENCES instansi (id),
            FOREIGN KEY (penilai_id) REFERENCES penilai (id)
        )
    ''')
    conn.commit()
    conn.close()

# Panggil fungsi init database
init_db()

def get_tahun_laporan(data_ak, data_pegawai, fallback_year=None):
    """
    Mengambil tahun yang akan digunakan di nomor laporan.
    Prioritas:
      1. Dari kolom 'tanggal_ditetapkan' di data_ak (jika ada)
      2. Dari 'tanggal_akhir_penilaian' di data_ak (jika ada)
      3. Dari 'tanggal_ditetapkan' di data_pegawai (jika ada)
      4. fallback_year (default: tahun sekarang)
    """
    if fallback_year is None:
        fallback_year = datetime.now().year

    # Coba dari data_ak (ambil yang pertama)
    if not data_ak.empty and 'tanggal_ditetapkan' in data_ak.columns:
        tgl_ditetapkan = data_ak['tanggal_ditetapkan'].iloc[0]
        if pd.notna(tgl_ditetapkan):
            try:
                return pd.to_datetime(tgl_ditetapkan).year
            except:
                pass

    if not data_ak.empty and 'tanggal_akhir_penilaian' in data_ak.columns:
        tgl_akhir = data_ak['tanggal_akhir_penilaian'].iloc[0]
        if pd.notna(tgl_akhir):
            try:
                return pd.to_datetime(tgl_akhir).year
            except:
                pass

    # Coba dari data_pegawai
    tgl_ditetapkan_pegawai = data_pegawai.get('tanggal_ditetapkan')
    if tgl_ditetapkan_pegawai and pd.notna(pd.to_datetime(tgl_ditetapkan_pegawai, errors='coerce')):
        try:
            return pd.to_datetime(tgl_ditetapkan_pegawai).year
        except:
            pass

    # Fallback
    return fallback_year


# Fungsi untuk koneksi database
def get_connection():
    return sqlite3.connect('pegawai.db')

# Fungsi CRUD
def create_pegawai(data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO pegawai (
                nama, nip, no_seri_karpeg, tempat_lahir, tanggal_lahir,
                jenis_kelamin, pangkat, golongan, tmt_pangkat, jabatan,
                tmt_jabatan, unit_kerja
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def read_pegawai():
    conn = get_connection()
    df = pd.read_sql('SELECT * FROM pegawai', conn)
    conn.close()
    return df

def delete_pegawai(pegawai_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM pegawai WHERE id=?', (pegawai_id,))
    conn.commit()
    conn.close()

# Fungsi untuk mengambil data pegawai berdasarkan ID
def get_pegawai_by_id(pegawai_id):
    conn = get_connection()
    df = pd.read_sql('SELECT * FROM pegawai WHERE id = ?', conn, params=(pegawai_id,))
    conn.close()
    return df

# Fungsi untuk mengupdate data pegawai
def update_pegawai(data):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = '''
            UPDATE pegawai 
            SET nama=?, nip=?, no_seri_karpeg=?, tempat_lahir=?, tanggal_lahir=?, 
                jenis_kelamin=?, pangkat=?, golongan=?, tmt_pangkat=?, 
                jabatan=?, tmt_jabatan=?, unit_kerja=?
            WHERE id=?
        '''
        cursor.execute(query, data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error updating employee: {e}")
        return False
    finally:
        conn.close()

# Fungsi CRUD untuk Instansi
def create_instansi(nama_instansi):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO instansi (nama_instansi) VALUES (?)', (nama_instansi,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def read_instansi():
    conn = get_connection()
    df = pd.read_sql('SELECT * FROM instansi', conn)
    conn.close()
    return df

def update_instansi(instansi_id, nama_instansi):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE instansi SET nama_instansi=? WHERE id=?', (nama_instansi, instansi_id))
    conn.commit()
    conn.close()

def delete_instansi(instansi_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM instansi WHERE id=?', (instansi_id,))
    conn.commit()
    conn.close()

def get_instansi_by_id(instansi_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM instansi WHERE id=?', (instansi_id,))
    result = c.fetchone()
    conn.close()
    return result

# Fungsi CRUD untuk Penilai
def create_penilai(data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO penilai (
                nama, nip, no_seri_karpeg, tempat_lahir, tanggal_lahir,
                jenis_kelamin, pangkat, golongan, tmt_pangkat, jabatan,
                tmt_jabatan, unit_kerja
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def read_penilai():
    conn = get_connection()
    df = pd.read_sql('SELECT * FROM penilai', conn)
    conn.close()
    return df

def update_penilai(penilai_id, data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE penilai SET
            nama=?, nip=?, no_seri_karpeg=?, tempat_lahir=?, tanggal_lahir=?,
            jenis_kelamin=?, pangkat=?, golongan=?, tmt_pangkat=?, jabatan=?,
            tmt_jabatan=?, unit_kerja=?
        WHERE id=?
    ''', (*data, penilai_id))
    conn.commit()
    conn.close()

def delete_penilai(penilai_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM penilai WHERE id=?', (penilai_id,))
    conn.commit()
    conn.close()

def get_penilai_by_id(penilai_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM penilai WHERE id=?', (penilai_id,))
    result = c.fetchone()
    conn.close()
    return result

# Fungsi CRUD untuk Angka Integrasi
def create_angka_integrasi(pegawai_id, jumlah_angka_integrasi):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO angka_integrasi (pegawai_id, jumlah_angka_integrasi) VALUES (?, ?)', (pegawai_id, jumlah_angka_integrasi))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def read_angka_integrasi():
    conn = get_connection()
    df = pd.read_sql('''
        SELECT ai.id, p.nama, p.nip, ai.jumlah_angka_integrasi
        FROM angka_integrasi ai
        JOIN pegawai p ON ai.pegawai_id = p.id
    ''', conn)
    conn.close()
    return df

def update_angka_integrasi(angka_integrasi_id, pegawai_id, jumlah_angka_integrasi):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE angka_integrasi SET pegawai_id=?, jumlah_angka_integrasi=? WHERE id=?', (pegawai_id, jumlah_angka_integrasi, angka_integrasi_id))
    conn.commit()
    conn.close()

def delete_angka_integrasi(angka_integrasi_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM angka_integrasi WHERE id=?', (angka_integrasi_id,))
    conn.commit()
    conn.close()

def get_angka_integrasi_by_id(angka_integrasi_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM angka_integrasi WHERE id=?', (angka_integrasi_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_pegawai_options():
    conn = get_connection()
    df = pd.read_sql('SELECT id, nama, nip FROM pegawai', conn)
    conn.close()
    return df

# Fungsi CRUD untuk AK
def create_ak(data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO ak (
                pegawai_id, instansi_id, penilai_id, tanggal_awal_penilaian,
                tanggal_akhir_penilaian, penilaian, prosentase, koefisien, jumlah_angka_kredit, tanggal_ditetapkan, tempat_ditetapkan, jenjang
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def read_ak():
    conn = get_connection()
    df = pd.read_sql('''
        SELECT ak.id, p.nama as nama_pegawai, p.nip, i.nama_instansi,
               pen.nama as nama_penilai, ak.tanggal_awal_penilaian,
               ak.tanggal_akhir_penilaian, ak.penilaian, ak.prosentase, ak.koefisien, ak.jumlah_angka_kredit, ak.tanggal_ditetapkan,
               ak.tempat_ditetapkan, ak.jenjang
        FROM ak
        JOIN pegawai p ON ak.pegawai_id = p.id
        JOIN instansi i ON ak.instansi_id = i.id
        JOIN penilai pen ON ak.penilai_id = pen.id
    ''', conn)
    conn.close()
    return df

def update_ak(ak_id, data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE ak SET
            pegawai_id=?, instansi_id=?, penilai_id=?, tanggal_awal_penilaian=?,
            tanggal_akhir_penilaian=?, penilaian=?, prosentase=?, koefisien=?, jumlah_angka_kredit=?, tanggal_ditetapkan=?, tempat_ditetapkan=?, jenjang=?
        WHERE id=?
    ''', (*data, ak_id))
    conn.commit()
    conn.close()

def delete_ak(ak_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM ak WHERE id=?', (ak_id,))
    conn.commit()
    conn.close()

def get_ak_by_id(ak_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM ak WHERE id=?', (ak_id,))
    result = c.fetchone()
    conn.close()
    return result

def get_instansi_options():
    conn = get_connection()
    df = pd.read_sql('SELECT id, nama_instansi FROM instansi', conn)
    conn.close()
    return df

def get_penilai_options():
    conn = get_connection()
    df = pd.read_sql('SELECT id, nama, nip FROM penilai', conn)
    conn.close()
    return df

def get_ak_data_for_report(pegawai_id=None, tgl_awal=None, tgl_akhir=None):
    conn = get_connection()
    query = '''
        SELECT 
            p.nama as nama_pegawai,
            p.nip,
            p.no_seri_karpeg,
            p.tempat_lahir,
            p.tanggal_lahir,
            p.jenis_kelamin,
            p.pangkat,
            p.golongan,
            p.tmt_pangkat,
            p.jabatan,
            p.tmt_jabatan,
            p.unit_kerja,
            i.nama_instansi,
            pen.nama as nama_penilai,
            pen.nip as nip_penilai,
            ak.tanggal_awal_penilaian,
            ak.tanggal_akhir_penilaian,
            ak.penilaian,
            ak.prosentase,
            ak.koefisien,
            ak.jumlah_angka_kredit,
            ak.tanggal_ditetapkan,
            ak.tempat_ditetapkan,
            ak.jenjang
        FROM ak
        JOIN pegawai p ON ak.pegawai_id = p.id
        JOIN instansi i ON ak.instansi_id = i.id
        JOIN penilai pen ON ak.penilai_id = pen.id
    '''
    params = []
    conditions = [] # Menggunakan list untuk membangun klausa WHERE
    if pegawai_id:
        conditions.append('p.id = ?')
        params.append(pegawai_id)
    # --- LOGIKA FILTER TANGGAL BARU ---
    if tgl_awal:
        # Filter data yang tanggal awalnya SAMA DENGAN tgl_awal
        conditions.append('ak.tanggal_awal_penilaian = ?')
        params.append(tgl_awal)
    if tgl_akhir:
        # Filter data yang tanggal akhirnya SAMA DENGAN tgl_akhir
        conditions.append('ak.tanggal_akhir_penilaian = ?')
        params.append(tgl_akhir)
    # --- AKHIR LOGIKA BARU ---
    # Gabungkan semua kondisi dengan 'AND'
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def get_angka_integrasi_for_report(pegawai_id):
    conn = get_connection()
    df = pd.read_sql('''
        SELECT jumlah_angka_integrasi
        FROM angka_integrasi
        WHERE pegawai_id = ?
    ''', conn, params=(pegawai_id,))
    conn.close()
    return df

def get_pegawai_data_for_report(pegawai_id):
    """Mengambil data lengkap pegawai termasuk instansi dan penilai default (jika ada) untuk keperluan laporan."""
    conn = get_connection()
    # Coba ambil dari data AK terbaru (untuk dapatkan instansi & penilai)
    df_ak = pd.read_sql('''
        SELECT 
            p.nama as nama_pegawai,
            p.nip,
            p.no_seri_karpeg,
            p.tempat_lahir,
            p.tanggal_lahir,
            p.jenis_kelamin,
            p.pangkat,
            p.golongan,
            p.tmt_pangkat,
            p.jabatan,
            p.tmt_jabatan,
            p.unit_kerja,
            i.nama_instansi,
            pen.nama as nama_penilai,
            pen.nip as nip_penilai,
            ak.tanggal_ditetapkan,
            ak.tempat_ditetapkan
        FROM ak
        JOIN pegawai p ON ak.pegawai_id = p.id
        JOIN instansi i ON ak.instansi_id = i.id
        JOIN penilai pen ON ak.penilai_id = pen.id
        WHERE p.id = ?
        ORDER BY ak.tanggal_ditetapkan DESC
        LIMIT 1
    ''', conn, params=(pegawai_id,))
    
    if not df_ak.empty:
        conn.close()
        return df_ak.iloc[0].to_dict()
    
    # Jika tidak ada AK, ambil data pegawai saja, dan isi field lain dengan dummy/default
    df_peg = pd.read_sql('SELECT * FROM pegawai WHERE id = ?', conn, params=(pegawai_id,))
    conn.close()
    
    if not df_peg.empty:
        data = df_peg.iloc[0].to_dict()
        # Tambahkan field yang dibutuhkan laporan
        data.update({
            'nama_instansi': '',
            'nama_penilai': '',
            'nip_penilai': '',
            'tanggal_ditetapkan': None,
            'tempat_ditetapkan': ''
        })
        return data
    
    return {}

def generate_penetapan_html(data_pegawai, data_ak, include_angka_integrasi=False, angka_integrasi_value=0.0):
    # --- Ambil tahun untuk nomor laporan ---
    if not data_ak.empty and 'tanggal_akhir_penilaian' in data_ak.columns:
        try:
            tahun = pd.to_datetime(data_ak['tanggal_akhir_penilaian'].iloc[0]).year
        except:
            tahun = datetime.now().year
    else:
        try:
            if data_pegawai.get('tanggal_ditetapkan'):
                tahun = pd.to_datetime(data_pegawai['tanggal_ditetapkan']).year
            else:
                tahun = datetime.now().year
        except:
            tahun = datetime.now().year

    # --- Hitung total angka kredit ---
    GOLONGAN_TO_LAMA = {
        "III/a": 0.0,
        "III/b": 50.0,
        "III/c": 0.0,
        "III/d": 100.0,
    }
    golongan = data_pegawai.get('golongan', '').strip()
    total_lama = GOLONGAN_TO_LAMA.get(golongan, 0.0)
    total_baru = data_ak['jumlah_angka_kredit'].sum() if not data_ak.empty else 0.0
    if include_angka_integrasi and angka_integrasi_value > 0:
        total_baru += angka_integrasi_value
    total_jumlah = total_lama + total_baru

    # --- Logika minimal AK ---
    MINIMAL_AK_MAPPING = {
        ("III/a", "III/b"): (50, 100),
        ("III/b", "III/c"): (100, 100),
        ("III/c", "III/d"): (100, 200),
        ("III/d", "IV/a"): (200, 200),
        ("IV/a", "IV/b"): (150, 450),
        ("IV/b", "IV/c"): (300, 450),
        ("IV/c", "IV/d"): (450, 450),
        ("IV/d", "IV/e"): (200, 0),
    }
    GOLONGAN_HIERARKI = ["III/a", "III/b", "III/c", "III/d", "IV/a", "IV/b", "IV/c", "IV/d", "IV/e"]
    PANGKAT_OPTIONS_REVERSE = {v: k for k, v in PANGKAT_OPTIONS.items()}

    golongan = data_pegawai.get('golongan', '').strip()
    next_golongan = "N/A"
    pangkat_minimal = 0.0
    jenjang_minimal = 0.0
    if golongan in GOLONGAN_HIERARKI:
        idx = GOLONGAN_HIERARKI.index(golongan)
        if idx < len(GOLONGAN_HIERARKI) - 1:
            next_golongan = GOLONGAN_HIERARKI[idx + 1]
            key = (golongan, next_golongan)
            if key in MINIMAL_AK_MAPPING:
                pangkat_minimal, jenjang_minimal = MINIMAL_AK_MAPPING[key]
        else:
            next_golongan = "Tertinggi"

    if next_golongan in GOLONGAN_HIERARKI:
        nama_pangkat_tujuan = PANGKAT_OPTIONS_REVERSE.get(next_golongan, next_golongan)
        teks_tujuan = f"{nama_pangkat_tujuan} {next_golongan}"
    else:
        teks_tujuan = next_golongan

    hasil_pangkat = total_jumlah - pangkat_minimal
    hasil_jenjang = total_jumlah - jenjang_minimal

    # === ✅ AMBIL JENJANG DARI data_ak ===
    jenjang_raw = ""
    if not data_ak.empty and 'jenjang' in data_ak.columns:
        jenjang_raw = data_ak['jenjang'].iloc[0] or ''

    # === KONVERSI KE FORMAT JABATAN FUNGSIONAL ===
    def jenjang_to_jabatan(jenjang_str):
        if not jenjang_str:
            return "Analis"
        if jenjang_str.startswith("KEAHLIAN"):
            # Contoh: "KEAHLIAN - AHLI PERTAMA" → "Analis Ahli Pertama"
            suffix = jenjang_str.replace("KEAHLIAN - AHLI ", "").title()
            return f"Analis Ahli {suffix}"
        elif jenjang_str.startswith("KETERAMPILAN"):
            # Contoh: "KETERAMPILAN - TERAMPIL" → "Analis Terampil"
            suffix = jenjang_str.replace("KETERAMPILAN - ", "").title()
            return f"Analis {suffix}"
        else:
            return "Analis"

    # Use the actual job title from the employee record instead of defaulting to "Analis"
    # jabatan_fungsional = jenjang_to_jabatan(jenjang_raw)

    # === FORMAT TMT ===
    tmt_jabatan_str = ""
    tmt_jabatan_val = data_pegawai.get('tmt_jabatan')
    if tmt_jabatan_val and pd.notna(pd.to_datetime(tmt_jabatan_val, dayfirst=True, errors='coerce')):
        tmt_jabatan_str = pd.to_datetime(tmt_jabatan_val, dayfirst=True).strftime('%d-%m-%Y')

    # === GABUNGKAN ===
    jabatan_actual = data_pegawai.get('jabatan', 'Analis')  # Fallback to 'Analis' if no job title
    if tmt_jabatan_str:
        jabatan_dan_tmt = f"{jabatan_actual} / {tmt_jabatan_str}"
    else:
        jabatan_dan_tmt = jabatan_actual

    # === FORMAT PERIODE ===
    periode_awal_str = ''
    periode_akhir_str = ''
    if not data_ak.empty:
        if 'tanggal_awal_penilaian' in data_ak.columns:
            periode_awal_str = pd.to_datetime(data_ak['tanggal_awal_penilaian'].min()).strftime('%d-%m-%Y')
        if 'tanggal_akhir_penilaian' in data_ak.columns:
            periode_akhir_str = pd.to_datetime(data_ak['tanggal_akhir_penilaian'].max()).strftime('%d-%m-%Y')

    # === GENERATE HTML ===
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Penetapan Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 0; margin-bottom: 0; table-layout: fixed; }}
            th, td {{ border: 1px solid black; padding: 2px; text-align: left; word-wrap: break-word; }}
            .label {{ display: inline-block; width: 200px; text-align: left; }}
            .colon {{ margin-left: 5px; margin-right: 5px; }}
            .value {{ display: inline-block; }}
            .inline-container {{ white-space: nowrap; margin: 0; padding: 0; }}
            .left-align, .right-align {{ display: inline-block; width: 49%; margin: 0; padding: 0; }}
            .left-align {{ text-align: left; }}
            .right-align {{ text-align: right; }}
        </style>
    </head>
    <body>
        <p style="text-align: center; margin: 0; padding: 0;">
            <b>
                PENETAPAN ANGKA KREDIT<br>
                NOMOR : 800/ ...... /......../Dindik/{tahun}/PAK
            </b>
        </p>
        <br><br><br>
        <div class="inline-container">
            <div class="left-align">
                Instansi : {data_pegawai.get('nama_instansi', '')}
            </div>
            <div class="right-align">
                Periode : {periode_awal_str} s.d. {periode_akhir_str}
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="text-align: center; width: 5%;">I.</th>
                    <th style="text-align: center; width: 95%;" colspan="2">KETERANGAN PERORANGAN</th>
                </tr>
            </thead>
            <tbody>
                <tr><td style="width: 5%; text-align: center">1.</td><td colspan="2"><span class="label">Nama</span><span class="colon">:</span><span class="value">{data_pegawai.get('nama_pegawai', '')}</span></td></tr>
                <tr><td style="text-align: center">2.</td><td colspan="2"><span class="label">NIP</span><span class="colon">:</span><span class="value">{data_pegawai.get('nip', '')}</span></td></tr>
                <tr><td style="text-align: center">3.</td><td colspan="2"><span class="label">No. Seri Karpeg</span><span class="colon">:</span><span class="value">{data_pegawai.get('no_seri_karpeg', '')}</span></td></tr>
                <tr><td style="text-align: center">4.</td><td colspan="2"><span class="label">Tempat Tgl. Lahir</span><span class="colon">:</span><span class="value">{data_pegawai.get('tempat_lahir', '')}, {pd.to_datetime(data_pegawai.get('tanggal_lahir'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tanggal_lahir') and pd.notna(pd.to_datetime(data_pegawai.get('tanggal_lahir'), dayfirst=True)) else ''}</span></td></tr>
                <tr><td style="text-align: center">5.</td><td colspan="2"><span class="label">Jenis Kelamin</span><span class="colon">:</span><span class="value">{data_pegawai.get('jenis_kelamin', '')}</span></td></tr>
                <tr><td style="text-align: center">6.</td><td colspan="2"><span class="label">Pangkat/Golongan ruang/TMT</span><span class="colon">:</span><span class="value">{data_pegawai.get('pangkat', '')} ({data_pegawai.get('golongan', '')}), {pd.to_datetime(data_pegawai.get('tmt_pangkat'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tmt_pangkat') and pd.notna(pd.to_datetime(data_pegawai.get('tmt_pangkat'), dayfirst=True)) else ''}</span></td></tr>
                <tr><td style="text-align: center">7.</td><td colspan="2"><span class="label">Jabatan /TMT</span><span class="colon">:</span><span class="value">{jabatan_dan_tmt}</span></td></tr>
                <tr><td style="text-align: center">8.</td><td colspan="2"><span class="label">Unit Kerja</span><span class="colon">:</span><span class="value">{data_pegawai.get('unit_kerja', '')}</span></td></tr>
                <tr><th style="text-align: center; border-bottom: none;" colspan="3">HASIL PENILAIAN ANGKA KREDIT</th></tr>
            </tbody>
        </table>
        <table>
            <thead>
                <tr>
                    <th style="text-align: center; width: 5%;">II.</th>
                    <th style="text-align: center; width: 45%;">PENETAPAN ANGKA KREDIT</th>
                    <th style="text-align: center; width: 10%;">LAMA</th>
                    <th style="text-align: center; width: 10%;">BARU</th>
                    <th style="text-align: center; width: 10%;">JUMLAH</th>
                    <th style="text-align: center; width: 20%;">KETERANGAN</th>
                </tr>
                <tr>
                    <th style="text-align: center">1</th>
                    <th style="text-align: center">2</th>
                    <th style="text-align: center">3</th>
                    <th style="text-align: center">4</th>
                    <th style="text-align: center">5</th>
                    <th style="text-align: center">6</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="text-align: center; width: 5%;">1.</td>
                    <td style="width: 45%;">AK dasar yang diberikan</td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 20%;"></td>
                </tr>
                <tr>
                    <td style="text-align: center; width: 5%;">2.</td>
                    <td style="width: 45%;">AK konversi dari predikat</td>
                    <td style="text-align: center; width: 10%;">{total_lama:.3f}</td>
                    <td style="text-align: center; width: 10%;">{total_baru:.3f}</td>
                    <td style="text-align: center; width: 10%;">{total_jumlah:.3f}</td>
                    <td style="text-align: center; width: 20%;"></td>
                </tr>
                <tr>
                    <td style="text-align: center; width: 5%;">3.</td>
                    <td style="width: 45%;">AK penyesuaian penyetaraan</td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 20%;"></td>
                </tr>
                <tr>
                    <td style="text-align: center; width: 5%;">4.</td>
                    <td style="width: 45%;">AK yang diperoleh dari peningkatan pendidikan</td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 10%;"></td>
                    <td style="text-align: center; width: 20%;"></td>
                </tr>
                <tr>
                    <td style="text-align: center; width: 5%;">5.</td>
                    <td style="width: 45%;">-</td>
                    <td style="text-align: center; width: 10%;">-</td>
                    <td style="text-align: center; width: 10%;">-</td>
                    <td style="text-align: center; width: 10%;">-</td>
                    <td style="text-align: center; width: 20%;">-</td>
                </tr>
                <tr>
                    <td style="text-align: center; width: 5%;">6.</td>
                    <td style="width: 45%;">JUMLAH</td>
                    <td style="text-align: center; width: 10%;">{total_lama:.3f}</td>
                    <td style="text-align: center; width: 10%;">{total_baru:.3f}</td>
                    <td style="text-align: center; width: 10%;">{total_jumlah:.3f}</td>
                    <td style="text-align: center; width: 20%;"></td>
                </tr>
            </tbody>
            <thead>
                <tr>
                    <th colspan="6" style="text-align: center">KONVERSI KE ANGKA KREDIT</th>
                </tr>
                <tr>
                    <th colspan="2" style="text-align: center">Keterangan</th>
                    <th colspan="2" style="text-align: center">Pangkat</th>
                    <th colspan="2" style="text-align: center">Jenjang Jabatan</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="2" style="width: 250px">Angka Kredit minimal yang harus dipenuhi untuk kenaikan pangkat / jenjang</td>
                    <td colspan="2" style="text-align: center">{pangkat_minimal:.3f}</td>
                    <td colspan="2" style="text-align: center">{jenjang_minimal:.3f}</td>
                </tr>
                <tr>
                    <td colspan="2">
                        {'Kelebihan/<del>Kekurangan</del>' if hasil_pangkat > 0 else '<del>Kelebihan</del>/Kekurangan'} *) Angka Kredit yang harus dicapai untuk kenaikan pangkat
                    </td>
                    <td colspan="2" style="text-align: center">{hasil_pangkat:.3f}</td>
                    <td colspan="2"></td>
                </tr>
                <tr>
                    <td colspan="2">
                        {'Kelebihan/<del>Kekurangan</del>' if hasil_jenjang > 0 else '<del>Kelebihan</del>/Kekurangan'} *) Angka Kredit yang harus dicapai untuk kenaikan jenjang
                    </td>
                    <td colspan="2"></td>
                    <td colspan="2" style="text-align: center">{hasil_jenjang:.3f}</td>
                </tr>
                <tr>
                    <td colspan="6" style="text-align: justify">
                        <b><i>{'Dapat' if hasil_pangkat > 0 else 'Tidak dapat'}</i></b>
                        dipertimbangkan untuk kenaikan Pangkat/Jabatan setingkat lebih tinggi ke
                        <b><i>{teks_tujuan}</i></b>
                    </td>
                </tr>
            </tbody>
        </table>
        <br><br>
        <table>
            <tr>
                <td style="border: none;width:65%">
                    ASLI disampaikan dengan hormat kepada: <br>
                    Jabatan Fungsional yang bersangkutan. <br><br>
                    Tembusan disampaikan kepada: <br>
                    1. Pimpinan Unit Kerja; <br>
                    2. Pejabat Penilai Kinerja;<br>
                    3. Sekretaris Tim Penilai yang bersangkutan; dan <br>
                    4. Kepala Biro Kepegawaian dan Organisasi.
                </td>
                <td style="border: none;">
                    Ditetapkan di {data_pegawai.get('tempat_ditetapkan', '')} <br>
                    Pada tanggal, {pd.to_datetime(data_pegawai.get('tanggal_ditetapkan'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tanggal_ditetapkan') and pd.notna(pd.to_datetime(data_pegawai.get('tanggal_ditetapkan'), dayfirst=True)) else ''}. <br><br>
                    Pejabat Penilai Kinerja <br><br><br><br>
                    {data_pegawai.get('nama_penilai', '')} <br>
                    NIP. {data_pegawai.get('nip_penilai', '')}
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

def generate_akumulasi_html(data_pegawai, data_ak, include_angka_integrasi=False, angka_integrasi_value=0.0):
    # --- Ambil tahun untuk nomor laporan ---
    if not data_ak.empty and 'tanggal_akhir_penilaian' in data_ak.columns:
        try:
            tahun = pd.to_datetime(data_ak['tanggal_akhir_penilaian'].iloc[0]).year
        except:
            tahun = datetime.now().year
    else:
        try:
            if data_pegawai.get('tanggal_ditetapkan'):
                tahun = pd.to_datetime(data_pegawai['tanggal_ditetapkan']).year
            else:
                tahun = datetime.now().year
        except:
            tahun = datetime.now().year

    # === ✅ Ambil jenjang dari data_ak ===
    jenjang_raw = ""
    if not data_ak.empty and 'jenjang' in data_ak.columns:
        jenjang_raw = data_ak['jenjang'].iloc[0] or ''

    def jenjang_to_jabatan(jenjang_str):
        if not jenjang_str:
            return "Analis"
        if jenjang_str.startswith("KEAHLIAN"):
            suffix = jenjang_str.replace("KEAHLIAN - AHLI ", "").title()
            return f"Analis Ahli {suffix}"
        elif jenjang_str.startswith("KETERAMPILAN"):
            suffix = jenjang_str.replace("KETERAMPILAN - ", "").title()
            return f"Analis {suffix}"
        else:
            return "Analis"

    # Use the actual job title from the employee record instead of defaulting to "Analis"
    # jabatan_fungsional = jenjang_to_jabatan(jenjang_raw)

    # === Format TMT Jabatan ===
    tmt_jabatan_str = ""
    tmt_jabatan_val = data_pegawai.get('tmt_jabatan')
    if tmt_jabatan_val and pd.notna(pd.to_datetime(tmt_jabatan_val, dayfirst=True, errors='coerce')):
        tmt_jabatan_str = pd.to_datetime(tmt_jabatan_val, dayfirst=True).strftime('%d-%m-%Y')

    jabatan_actual = data_pegawai.get('jabatan', 'Analis')  # Fallback to 'Analis' if no job title
    jabatan_dan_tmt = f"{jabatan_actual} / {tmt_jabatan_str}" if tmt_jabatan_str else jabatan_actual

    # === Format periode ===
    periode_awal_str = ''
    periode_akhir_str = ''
    if not data_ak.empty and 'tanggal_awal_penilaian' in data_ak.columns:
        periode_awal_str = pd.to_datetime(data_ak['tanggal_awal_penilaian'].min()).strftime('%d-%m-%Y')
    if not data_ak.empty and 'tanggal_akhir_penilaian' in data_ak.columns:
        periode_akhir_str = pd.to_datetime(data_ak['tanggal_akhir_penilaian'].max()).strftime('%d-%m-%Y')

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Akumulasi Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 0; margin-bottom: 0; }}
            th, td {{ border: solid 1px black; padding: 5px; text-align: left; }}
            th {{ background-color: none; color: black; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .label {{ display: inline-block; width: 200px; text-align: left; }}
            .colon {{ margin-left: 5px; margin-right: 5px; }}
            .value {{ display: inline-block; }}
            .inline-container {{ white-space: nowrap; margin: 0; padding: 0; }}
            .left-align, .right-align {{ display: inline-block; width: 49%; margin: 0; padding: 0; }}
            .left-align {{ text-align: left; }}
            .right-align {{ text-align: right; }}
        </style>
    </head>
    <body>
        <p style="text-align: center; margin: 0; padding: 0;">
            <b>
                AKUMULASI ANGKA KREDIT<br>
                NOMOR : 800/ ...... / ...... /Dindik/{tahun}/PAK
            </b>
        </p>
        <br><br><br>
        <div class="inline-container">
            <div class="left-align">
                Instansi : {data_pegawai.get('nama_instansi', '')}
            </div>
            <div class="right-align">
                Periode : {periode_awal_str} s.d. {periode_akhir_str}
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="text-align: center">I.</th>
                    <th colspan="2">KETERANGAN PERORANGAN</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="width: 20px; text-align: center">1.</td>
                    <td colspan="2">
                        <span class="label">Nama</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('nama_pegawai', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">2.</td>
                    <td colspan="2">
                        <span class="label">NIP</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('nip', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">3.</td>
                    <td colspan="2">
                        <span class="label">No. Seri Karpeg</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('no_seri_karpeg', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">4.</td>
                    <td colspan="2">
                        <span class="label">Tempat Tgl. Lahir</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('tempat_lahir', '')}, {pd.to_datetime(data_pegawai.get('tanggal_lahir'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tanggal_lahir') and pd.notna(pd.to_datetime(data_pegawai.get('tanggal_lahir'), dayfirst=True)) else ''}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">5.</td>
                    <td colspan="2">
                        <span class="label">Jenis Kelamin</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('jenis_kelamin', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">6.</td>
                    <td colspan="2">
                        <span class="label">Pangkat/Golongan ruang/TMT</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('pangkat', '')}, {data_pegawai.get('golongan', '')}, {pd.to_datetime(data_pegawai.get('tmt_pangkat'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tmt_pangkat') and pd.notna(pd.to_datetime(data_pegawai.get('tmt_pangkat'), dayfirst=True)) else ''}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">7.</td>
                    <td colspan="2">
                        <span class="label">Jabatan /TMT</span>
                        <span class="colon">:</span>
                        <span class="value">{jabatan_dan_tmt}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">8.</td>
                    <td colspan="2">
                        <span class="label">Unit Kerja</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('unit_kerja', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">9.</td>
                    <td colspan="2">
                        <span class="label">Instansi</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('nama_instansi', '')}</span>
                    </td>
                </tr>
                <tr>
                    <th style="text-align: center; border-bottom: none;" colspan="3">Konversi KE ANGKA KREDIT</th>
                </tr>
            </tbody>
        </table>
        <table>
            <thead>
                <tr class="baris">
                    <th style="vertical-align:middle; text-align:center" colspan="4" class="header-cell">HASIL PENILAIAN KINERJA</th>
                    <th style="vertical-align:middle; text-align:center">KOEFSIEN <br> PER TAHUN</th>
                    <th style="vertical-align:middle; text-align:center">ANGKA KREDIT <br> YANG DI DAPAT</th>
                </tr>
                <tr>
                    <th style="vertical-align:middle; text-align:center">TAHUN</th>
                    <th style="vertical-align:middle; text-align:center">PERIODIK <br> BULAN</th>
                    <th style="vertical-align:middle; text-align:center">PREDIKAT</th>
                    <th style="vertical-align:middle; text-align:center">PROSENTASE</th>
                    <th style="vertical-align:middle; text-align:center">5</th>
                    <th style="vertical-align:middle; text-align:center">6</th>
                </tr>
            </thead>
            <tbody>
    """
    total_angka_kredit = 0.0
    # Tambahkan baris "AK Integrasi" jika dipilih
    if include_angka_integrasi and angka_integrasi_value > 0:
        total_angka_kredit += angka_integrasi_value
        html += f"""
                <tr>
                    <td style="text-align: center;">AK Integrasi</td>
                    <td style="text-align: center;">-</td>
                    <td style="text-align: center;">-</td>
                    <td style="text-align: center;"></td>
                    <td style="text-align: center;"></td>
                    <td style="text-align: center;">{angka_integrasi_value:.3f}</td>
                </tr>
        """
    # Tambahkan data AK dari periode yang dipilih
    for i, (index, row) in enumerate(data_ak.iterrows(), 1):
        tanggal_awal = pd.to_datetime(row['tanggal_awal_penilaian'])
        tanggal_akhir = pd.to_datetime(row['tanggal_akhir_penilaian'])
        bulan = (tanggal_akhir.year - tanggal_awal.year) * 12 + (tanggal_akhir.month - tanggal_awal.month)
        if tanggal_akhir.day >= tanggal_awal.day:
            bulan += 1
        if bulan == 0:
            bulan = 1
        ak_value = row['jumlah_angka_kredit']
        total_angka_kredit += ak_value
        html += f"""
                <tr>
                    <td style="text-align: center;">{tanggal_awal.year}</td>
                    <td style="text-align: center;">{bulan} bulan</td>
                    <td style="text-align: center;">{row['penilaian']}</td>
                    <td style="text-align: center;">{row['prosentase']}%</td>
                    <td style="text-align: center;">{row['koefisien']}</td>
                    <td style="text-align: center;">{ak_value:.3f}</td>
                </tr>
        """
    html += f"""
                <tr>
                    <td colspan="5" style="text-align: right; font-weight: bold;">Jumlah Angka Kredit</td>
                    <td style="text-align: center; font-weight: bold;">{total_angka_kredit:.3f}</td>
                </tr>
            </tbody>
        </table>
        <br><br>
        <p style="padding-left:450px">
            Ditetapkan di {data_pegawai.get('tempat_ditetapkan', '')} <br>
            Pada tanggal, {pd.to_datetime(data_pegawai.get('tanggal_ditetapkan'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tanggal_ditetapkan') and pd.notna(pd.to_datetime(data_pegawai.get('tanggal_ditetapkan'), dayfirst=True)) else ''}. <br><br>
            Pejabat Penilai Kinerja <br><br><br><br>
            {data_pegawai.get('nama_penilai', '')} <br>
            NIP.{data_pegawai.get('nip_penilai', '')}
        </p>
        <br><br>
        <p>
            Tembusan disampaikan kepada: <br>
            1. Jabatan Fungsional yang bersangkutan <br>
            2. Ketua/atasan unit kerja <br>
            3. Kepala Biro Kepegawaian dan Organisasi <br>
            4. Pejabat lain yang dianggap perlu.
        </p>
    </body>
    </html>
    """
    return html

def generate_konversi_html(data_pegawai, data_ak, include_angka_integrasi=False, angka_integrasi_value=0.0):
    # --- Ambil tahun untuk nomor laporan ---
    if not data_ak.empty and 'tanggal_akhir_penilaian' in data_ak.columns:
        try:
            tahun = pd.to_datetime(data_ak['tanggal_akhir_penilaian'].iloc[0]).year
        except:
            tahun = datetime.now().year
    else:
        try:
            if data_pegawai.get('tanggal_ditetapkan'):
                tahun = pd.to_datetime(data_pegawai['tanggal_ditetapkan']).year
            else:
                tahun = datetime.now().year
        except:
            tahun = datetime.now().year

    # === ✅ Ambil jenjang dari data_ak ===
    jenjang_raw = ""
    if not data_ak.empty and 'jenjang' in data_ak.columns:
        jenjang_raw = data_ak['jenjang'].iloc[0] or ''

    def jenjang_to_jabatan(jenjang_str):
        if not jenjang_str:
            return "Analis"
        if jenjang_str.startswith("KEAHLIAN"):
            suffix = jenjang_str.replace("KEAHLIAN - AHLI ", "").title()
            return f"Analis Ahli {suffix}"
        elif jenjang_str.startswith("KETERAMPILAN"):
            suffix = jenjang_str.replace("KETERAMPILAN - ", "").title()
            return f"Analis {suffix}"
        else:
            return "Analis"

    # Use the actual job title from the employee record instead of defaulting to "Analis"
    # jabatan_fungsional = jenjang_to_jabatan(jenjang_raw)

    # === Format TMT Jabatan ===
    tmt_jabatan_str = ""
    tmt_jabatan_val = data_pegawai.get('tmt_jabatan')
    if tmt_jabatan_val and pd.notna(pd.to_datetime(tmt_jabatan_val, dayfirst=True, errors='coerce')):
        tmt_jabatan_str = pd.to_datetime(tmt_jabatan_val, dayfirst=True).strftime('%d-%m-%Y')

    jabatan_actual = data_pegawai.get('jabatan', 'Analis')  # Fallback to 'Analis' if no job title
    jabatan_dan_tmt = f"{jabatan_actual} / {tmt_jabatan_str}" if tmt_jabatan_str else jabatan_actual

    # === Format periode ===
    periode_awal_str = ''
    periode_akhir_str = ''
    if not data_ak.empty and 'tanggal_awal_penilaian' in data_ak.columns:
        periode_awal_str = pd.to_datetime(data_ak['tanggal_awal_penilaian'].min()).strftime('%d-%m-%Y')
    if not data_ak.empty and 'tanggal_akhir_penilaian' in data_ak.columns:
        periode_akhir_str = pd.to_datetime(data_ak['tanggal_akhir_penilaian'].max()).strftime('%d-%m-%Y')

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Konversi Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 0; margin-bottom: 0; }}
            th, td {{ border: 1px solid #0e0101; padding: 2px; text-align: left; }}
            th {{ background-color: none; color: black; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .label {{ display: inline-block; width: 200px; text-align: left; }}
            .colon {{ margin-left: 5px; margin-right: 5px; }}
            .value {{ display: inline-block; }}
            .inline-container {{ white-space: nowrap; margin: 0; padding: 0; }}
            .left-align, .right-align {{ display: inline-block; width: 49%; margin: 0; padding: 0; }}
            .left-align {{ text-align: left; }}
            .right-align {{ text-align: right; }}
        </style>
    </head>
    <body>
        <p style="text-align: center; margin: 0; padding: 0;">
            <b>
                KONVERSI KE ANGKA KREDIT<br>
                NOMOR : 800/ ...... /......../Dindik/{tahun}/PAK
            </b>
        </p>
        <br><br><br>
        <div class="inline-container">
            <div class="left-align">
                Instansi : {data_pegawai.get('nama_instansi', '')}
            </div>
            <div class="right-align">
                Periode : {periode_awal_str} s.d. {periode_akhir_str}
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="text-align: center">I.</th>
                    <th colspan="2">KETERANGAN PERORANGAN</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="width: 20px; text-align: center">1.</td>
                    <td colspan="2">
                        <span class="label">Nama</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('nama_pegawai', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">2.</td>
                    <td colspan="2">
                        <span class="label">NIP</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('nip', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">3.</td>
                    <td colspan="2">
                        <span class="label">No. Seri Karpeg</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('no_seri_karpeg', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">4.</td>
                    <td colspan="2">
                        <span class="label">Tempat Tgl. Lahir</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('tempat_lahir', '')}, {pd.to_datetime(data_pegawai.get('tanggal_lahir'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tanggal_lahir') and pd.notna(pd.to_datetime(data_pegawai.get('tanggal_lahir'), dayfirst=True)) else ''}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">5.</td>
                    <td colspan="2">
                        <span class="label">Jenis Kelamin</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('jenis_kelamin', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">6.</td>
                    <td colspan="2">
                        <span class="label">Pangkat/Golongan ruang/TMT</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('pangkat', '')}, {data_pegawai.get('golongan', '')}, {pd.to_datetime(data_pegawai.get('tmt_pangkat'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tmt_pangkat') and pd.notna(pd.to_datetime(data_pegawai.get('tmt_pangkat'), dayfirst=True)) else ''}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">7.</td>
                    <td colspan="2">
                        <span class="label">Jabatan /TMT</span>
                        <span class="colon">:</span>
                        <span class="value">{jabatan_dan_tmt}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">8.</td>
                    <td colspan="2">
                        <span class="label">Unit Kerja</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('unit_kerja', '')}</span>
                    </td>
                </tr>
                <tr>
                    <td style="text-align: center">9.</td>
                    <td colspan="2">
                        <span class="label">Instansi</span>
                        <span class="colon">:</span>
                        <span class="value">{data_pegawai.get('nama_instansi', '')}</span>
                    </td>
                </tr>
                <tr>
                    <th style="text-align: center; border-bottom: none;" colspan="3">Konversi KE ANGKA KREDIT</th>
            </tbody>
        </table>
        <table>
            <thead>
                <tr>
                    <th style="text-align: center" colspan="2">HASIL PENILAIAN KINERJA</th>
                    <th style="text-align: center">KOEFISIEN <br>PER TAHUN</th>
                    <th style="text-align: center">ANGKA KREDIT <br>YANG DI DAPAT</th>
                </tr>
                <tr>
                    <th style="text-align: center">PREDIKAT</th>
                    <th style="text-align: center">PROSENTASE</th>
                    <th style="text-align: center">3</th>
                    <th style="text-align: center">4</th>
                </tr>
            </thead>
            <tbody>
    """
    total_angka_kredit = 0.0
    # Tambahkan data AK biasa
    for index, row in data_ak.iterrows():
        total_angka_kredit += row['jumlah_angka_kredit']
        html += f"""
                <tr>
                    <td style="text-align: center">{row['penilaian']}</td>
                    <td style="text-align: center">{row['prosentase']}%</td>
                    <td style="text-align: center">{row['koefisien']}</td>
                    <td style="text-align: center">{row['jumlah_angka_kredit']:.3f}</td>
                </tr>
        """
    # Tambahkan baris Angka Integrasi jika dipilih
    if include_angka_integrasi and angka_integrasi_value > 0:
        total_angka_kredit += angka_integrasi_value
        html += f"""
                <tr>
                    <td style="text-align: center">AK Integrasi</td>
                    <td style="text-align: center"></td>
                    <td style="text-align: center"></td>
                    <td style="text-align: center">{angka_integrasi_value:.3f}</td>
                </tr>
        """
    html += f"""
                <tr>
                    <td colspan="3" style="text-align: right; font-weight: bold;">Jumlah Angka Kredit</td>
                    <td style="text-align: center; font-weight: bold;">{total_angka_kredit:.3f}</td>
                </tr>
            </tbody>
        </table>
        <br><br>
        <p style="padding-left:450px">
            Ditetapkan di {data_pegawai.get('tempat_ditetapkan', '')} <br>
            Pada tanggal, {pd.to_datetime(data_pegawai.get('tanggal_ditetapkan'), dayfirst=True).strftime('%d-%m-%Y') if data_pegawai.get('tanggal_ditetapkan') and pd.notna(pd.to_datetime(data_pegawai.get('tanggal_ditetapkan'), dayfirst=True)) else ''}. <br><br>
            Pejabat Penilai Kinerja <br><br><br><br>
            {data_pegawai.get('nama_penilai', '')} <br>
            NIP.{data_pegawai.get('nip_penilai', '')}
        </p>
        <br><br>
        <p>
            Tembusan disampaikan kepada: <br>
            1. Jabatan Fungsional yang bersangkutan <br>
            2. Ketua/atasan unit kerja <br>
            3. Kepala Biro Kepegawaian dan Organisasi <br>
            4. Pejabat lain yang dianggap perlu.
        </p>
    </body>
    </html>
    """
    return html

def html_to_pdf_with_weasyprint(html_content, nama_pegawai, tanggal_awal, tanggal_akhir):
    """Convert HTML content to PDF with custom naming convention using WeasyPrint"""
    try:
        from weasyprint import HTML, CSS
        from io import BytesIO

        # Create a BytesIO buffer to store the PDF
        pdf_buffer = BytesIO()

        # Convert HTML string to PDF
        HTML(string=html_content).write_pdf(pdf_buffer)

        # Get the PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        return pdf_bytes
    except ImportError:
        # Fallback to FPDF if weasyprint is not available
        return html_to_pdf_with_fpdf(html_content, nama_pegawai, tanggal_awal, tanggal_akhir)

def html_to_pdf_with_fpdf(html_content, nama_pegawai, tanggal_awal, tanggal_akhir):
    """Convert HTML content to PDF with custom naming convention using FPDF"""

    # Create PDF instance
    pdf = FPDF()
    pdf.add_page()

    # Add a basic font
    pdf.add_font('Arial', '', '', True)
    pdf.set_font('Arial', '', 12)

    # Since FPDF doesn't directly support HTML, we'll add the content as plain text
    # For a more advanced solution, we could use weasyprint or similar

    # For now, let's create a simplified version focusing on the key elements
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'KONVERSI KE ANGKA KREDIT', ln=True, align='C')
    pdf.ln(5)

    # Add employee info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Nama: {nama_pegawai}', ln=True)
    pdf.cell(0, 8, f'Periode: {tanggal_awal} s.d. {tanggal_akhir}', ln=True)
    pdf.ln(5)

    # Add the HTML content as plain text (simplified)
    # In a real implementation, we would parse the HTML properly
    lines = html_content.split('<br>')  # Simple split on br tags
    for line in lines:
        clean_line = line.replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', '')
        if clean_line.strip():
            pdf.cell(0, 8, clean_line.strip(), ln=True)

    # Return PDF bytes
    return pdf.output(dest='S').encode('latin-1')

def get_pdf_download_link(pdf_bytes, nama_pegawai, tanggal_awal, tanggal_akhir):
    """Generate a download link for the PDF with the specified naming convention"""
    # Format the filename according to the requirement
    filename = f"Konversi an.{nama_pegawai} periode {tanggal_awal} s.d {tanggal_akhir}.pdf"

    # Encode the PDF bytes to base64
    b64 = base64.b64encode(pdf_bytes).decode()

    # Create the download link
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download PDF</a>'

    return href

# Sidebar untuk navigasi
st.sidebar.title("📋 Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Menu:",
    ["🏠 Dashboard", "➕ Tambah Pegawai", "👁️ Lihat Data", "✏️ Edit Pegawai", "🗑️ Hapus Pegawai", "🏢 Kelola Instansi", "👨‍🏫 Kelola Penilai", "🔢 Kelola Angka Integrasi", "📋 Kelola AK", "📊 Laporan"]
)

# Halaman Dashboard
if menu == "🏠 Dashboard":
    st.header("Dashboard Data Pegawai")
    # Statistik data
    df = read_pegawai()
    total_pegawai = len(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pegawai", total_pegawai)
    with col2:
        if total_pegawai > 0:
            laki_laki = len(df[df['jenis_kelamin'] == 'Laki-laki'])
            st.metric("Pegawai Laki-laki", laki_laki)
    with col3:
        if total_pegawai > 0:
            perempuan = len(df[df['jenis_kelamin'] == 'Perempuan'])
            st.metric("Pegawai Perempuan", perempuan)
    # Tampilkan data terbaru
    if total_pegawai > 0:
        st.subheader("Data Pegawai Terbaru")
        st.dataframe(df.tail(5), use_container_width=True)
    else:
        st.info("Belum ada data pegawai. Silakan tambah data melalui menu 'Tambah Pegawai'.")

# Halaman Tambah Pegawai
elif menu == "➕ Tambah Pegawai":
    st.header("Tambah Data Pegawai Baru")
    # Select pangkat outside form for dynamic golongan update
    pangkat = st.selectbox("Pangkat", list(PANGKAT_OPTIONS.keys()), key='pangkat_tambah', on_change=update_golongan, args=('tambah',))
    with st.form("form_tambah_pegawai"):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap*")
            nip = st.text_input("NIP*")
            no_seri_karpeg = st.text_input("No. Seri Karpeg")
            tempat_lahir = st.text_input("Tempat Lahir*")
            tanggal_lahir = st.date_input("Tanggal Lahir*", max_value=datetime.now())
            jenis_kelamin = st.selectbox("Jenis Kelamin*", ["Laki-laki", "Perempuan"])
        with col2:
            golongan = st.text_input("Golongan", value=st.session_state.get('golongan_tambah', ''), disabled=True)
            tmt_pangkat = st.date_input("TMT Pangkat")
            jabatan = st.text_input("Jabatan")
            tmt_jabatan = st.date_input("TMT Jabatan")
            unit_kerja = st.text_input("Unit Kerja")
        submitted = st.form_submit_button("Simpan Data")
        if submitted:
            if not nama or not nip or not tempat_lahir:
                st.error("Harap isi field yang wajib diisi (*)")
            else:
                data = (
                    nama, nip, no_seri_karpeg, tempat_lahir,
                    tanggal_lahir, jenis_kelamin, st.session_state['pangkat_tambah'], st.session_state.get('golongan_tambah', ''),
                    tmt_pangkat, jabatan, tmt_jabatan, unit_kerja
                )
                if create_pegawai(data):
                    st.success("Data pegawai berhasil disimpan!")
                else:
                    st.error("NIP sudah terdaftar. Gunakan NIP yang berbeda.")

# Halaman Lihat Data
elif menu == "👁️ Lihat Data":
    st.header("👁️ Data Pegawai")
    # PASTIKAN BARIS INI ADA! Di sinilah 'df' didefinisikan.
    def get_all_pegawai_data():
        """Mengambil semua data dari tabel pegawai."""
        conn = get_connection()
        df = pd.read_sql('''
            SELECT 
                id, nama, nip, no_seri_karpeg, tempat_lahir, 
                tanggal_lahir, jenis_kelamin, pangkat, golongan, 
                tmt_pangkat, jabatan, tmt_jabatan, unit_kerja
            FROM pegawai
        ''', conn)
        conn.close()
        return df

    # 🚨 INI BARIS KRITIS YANG MENDIFINISIKAN df. PASTIKAN ADA DI SINI.
    df = get_all_pegawai_data()
    if not df.empty:
        # Format tanggal agar sesuai permintaan user (DD-MM-YYYY)
        if 'tanggal_lahir' in df.columns and pd.api.types.is_datetime64_any_dtype(df['tanggal_lahir'].dropna()):
            df['tanggal_lahir'] = pd.to_datetime(df['tanggal_lahir'], dayfirst=True).dt.strftime('%d-%m-%Y')
        elif 'tanggal_lahir' in df.columns:
            # Coba konversi jika kolomnya masih object/string
            df['tanggal_lahir'] = pd.to_datetime(df['tanggal_lahir'], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y').fillna('')
        if 'tmt_pangkat' in df.columns and pd.api.types.is_datetime64_any_dtype(df['tmt_pangkat'].dropna()):
            df['tmt_pangkat'] = pd.to_datetime(df['tmt_pangkat'], dayfirst=True).dt.strftime('%d-%m-%Y')
        elif 'tmt_pangkat' in df.columns:
             df['tmt_pangkat'] = pd.to_datetime(df['tmt_pangkat'], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y').fillna('')
        if 'tmt_jabatan' in df.columns and pd.api.types.is_datetime64_any_dtype(df['tmt_jabatan'].dropna()):
            df['tmt_jabatan'] = pd.to_datetime(df['tmt_jabatan'], dayfirst=True).dt.strftime('%d-%m-%Y')
        elif 'tmt_jabatan' in df.columns:
             df['tmt_jabatan'] = pd.to_datetime(df['tmt_jabatan'], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y').fillna('')
        # Ganti nama kolom untuk tampilan yang lebih rapi
        df.rename(columns={
            'id': 'ID',
            'nama': 'Nama',
            'nip': 'NIP',
            'no_seri_karpeg': 'No. Karpeg',
            'tempat_lahir': 'Tempat Lahir',
            'tanggal_lahir': 'Tanggal Lahir',
            'jenis_kelamin': 'J. Kelamin',
            'pangkat': 'Pangkat',
            'golongan': 'Golongan',
            'tmt_pangkat': 'TMT Pangkat',
            'jabatan': 'Jabatan',
            'tmt_jabatan': 'TMT Jabatan',
            'unit_kerja': 'Unit Kerja'
        }, inplace=True)
        st.dataframe(df, use_container_width=True)
        st.success(f"Total {len(df)} data pegawai ditemukan.")
    else:
        st.info("Tidak ada data pegawai yang tersimpan di database.")

elif menu == "✏️ Edit Pegawai":
    st.header("✏️ Edit Data Pegawai")
    df_pegawai = get_pegawai_options()
    if len(df_pegawai) > 0:
        pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
        selected_pegawai = st.selectbox("Pilih Pegawai untuk di Edit:", pegawai_options)
        if selected_pegawai:
            pegawai_id = int(selected_pegawai.split(" - ")[0])
            pegawai_data = get_pegawai_by_id(pegawai_id)
            # --- PASTIKAN INISIALISASI INI ADA DAN DI SINI ---
            error_tgl = False
            # Konversi data tanggal
            try:
                tmt_pangkat = pd.to_datetime(pegawai_data['tmt_pangkat'].iloc[0]).date()
                tmt_jabatan = pd.to_datetime(pegawai_data['tmt_jabatan'].iloc[0]).date()
                tanggal_lahir = pd.to_datetime(pegawai_data['tanggal_lahir'].iloc[0]).date()
            except Exception as e:
                # Jika terjadi error konversi tanggal (data tidak valid), set flag error
                st.error(f"Format tanggal di database tidak valid. Gagal memuat form edit. Error: {e}")
                error_tgl = True

            # Baris 1335 Anda seharusnya ada di sini:
            if not error_tgl:
                with st.form("edit_pegawai_form"):
                    st.subheader(f"Edit Data: {pegawai_data['nama'].iloc[0]}")
                    col1, col2 = st.columns(2)
                    # --- Kolom 1 ---
                    with col1:
                        new_nama = st.text_input("Nama*", value=pegawai_data['nama'].iloc[0])
                        # new_nip = st.text_input("NIP*", value=pegawai_data['nip'].iloc[0], disabled=True)
                        new_nip = st.text_input("NIP*", value=pegawai_data['nip'].iloc[0])
                        default_karpeg = pegawai_data['no_seri_karpeg'].iloc[0]
                        new_no_seri_karpeg = st.text_input("No. Seri Karpeg",
                                                          value=default_karpeg if pd.notna(default_karpeg) else '')
                        new_tempat_lahir = st.text_input("Tempat Lahir*", value=pegawai_data['tempat_lahir'].iloc[0])
                        new_tanggal_lahir = st.date_input("Tanggal Lahir*", value=tanggal_lahir)
                        default_pangkat = pegawai_data['pangkat'].iloc[0]
                        pangkat_index = list(PANGKAT_OPTIONS.keys()).index(default_pangkat) if default_pangkat in PANGKAT_OPTIONS else 0
                        new_pangkat = st.selectbox("Pangkat", list(PANGKAT_OPTIONS.keys()), index=pangkat_index, key='pangkat_edit')
                        if new_pangkat in PANGKAT_OPTIONS:
                            st.session_state['golongan_edit'] = PANGKAT_OPTIONS[new_pangkat]
                        else:
                            st.session_state['golongan_edit'] = pegawai_data['golongan'].iloc[0]

                    # --- Kolom 2 ---
                    with col2:
                        new_jenis_kelamin = st.selectbox("Jenis Kelamin*", ["Laki-laki", "Perempuan"], index=["Laki-laki", "Perempuan"].index(pegawai_data['jenis_kelamin'].iloc[0]))
                        new_golongan = st.text_input("Golongan", value=st.session_state.get('golongan_edit', pegawai_data['golongan'].iloc[0]), disabled=True)
                        new_tmt_pangkat = st.date_input("TMT Pangkat", value=tmt_pangkat)
                        new_jabatan = st.text_input("Jabatan", value=pegawai_data['jabatan'].iloc[0])
                        new_tmt_jabatan = st.date_input("TMT Jabatan", value=tmt_jabatan)
                        new_unit_kerja = st.text_input("Unit Kerja", value=pegawai_data['unit_kerja'].iloc[0])

                    submitted = st.form_submit_button("Update Data")
                    if submitted:
                        if not new_nama or not new_nip or not new_tempat_lahir:
                            st.error("Harap isi field yang wajib diisi (*)")
                        else:
                            data = (
                                new_nama, new_nip, new_no_seri_karpeg, new_tempat_lahir,
                                new_tanggal_lahir, new_jenis_kelamin, new_pangkat, new_golongan,
                                new_tmt_pangkat, new_jabatan, new_tmt_jabatan, new_unit_kerja, pegawai_id
                            )
                            if update_pegawai(data):
                                st.success(f"Data pegawai '{new_nama}' berhasil diupdate!")
                                st.rerun() # Ganti st.experimental_rerun() dengan st.rerun()
                            else:
                                st.error("Gagal mengupdate data pegawai. (Periksa log konsol jika NIP tidak berubah)")
    else:
        st.info("Belum ada data pegawai yang dapat di edit.")

# Halaman Hapus Pegawai
elif menu == "🗑️ Hapus Pegawai":
    st.header("🗑️ Hapus Data Pegawai")
    df_pegawai = get_pegawai_options()
    if len(df_pegawai) > 0:
        pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
        selected_pegawai = st.selectbox("Pilih Pegawai yang akan Dihapus:", pegawai_options)
        if selected_pegawai:
            pegawai_id = int(selected_pegawai.split(" - ")[0])
            pegawai_nama = selected_pegawai.split(" - ")[1].split(" (NIP:")[0]
            st.warning(f"Anda yakin ingin menghapus data pegawai: **{pegawai_nama}**?")
            st.info("Tindakan ini juga akan menghapus semua riwayat Angka Kredit (AK) yang terkait dengan pegawai ini.")
            # Tombol konfirmasi hapus
            if st.button(f"Konfirmasi Hapus Pegawai {pegawai_nama}", key="delete_confirm_btn"):
                if delete_pegawai(pegawai_id):
                    st.success(f"Data pegawai '{pegawai_nama}' dan semua riwayat AK berhasil dihapus!")
                    # Refresh halaman untuk memperbarui daftar
                    st.rerun() # Ganti st.experimental_rerun() dengan st.rerun()
                else:
                    st.error("Gagal menghapus data pegawai.")
    else:
        st.info("Tidak ada data pegawai yang dapat dihapus.")

# Halaman Kelola Instansi
elif menu == "🏢 Kelola Instansi":
    st.header("Kelola Data Instansi")
    submenu = st.sidebar.radio(
        "Pilih Submenu:",
        ["➕ Tambah Instansi", "👁️ Lihat Instansi", "✏️ Edit Instansi", "🗑️ Hapus Instansi"]
    )
    # Submenu Tambah Instansi
    if submenu == "➕ Tambah Instansi":
        st.subheader("Tambah Instansi Baru")
        with st.form("form_tambah_instansi"):
            nama_instansi = st.text_input("Nama Instansi*")
            submitted = st.form_submit_button("Simpan Instansi")
            if submitted:
                if not nama_instansi:
                    st.error("Harap isi nama instansi.")
                else:
                    if create_instansi(nama_instansi):
                        st.success("Instansi berhasil ditambahkan!")
                    else:
                        st.error("Nama instansi sudah terdaftar. Gunakan nama yang berbeda.")

    # Submenu Lihat Instansi
    elif submenu == "👁️ Lihat Instansi":
        st.subheader("Data Instansi")
        df_instansi = read_instansi()
        if len(df_instansi) > 0:
            # Filter data
            st.subheader("Filter Data")
            filter_nama = st.text_input("Cari berdasarkan nama instansi")
            # Terapkan filter
            filtered_df = df_instansi.copy()
            if filter_nama:
                filtered_df = filtered_df[filtered_df['nama_instansi'].str.contains(filter_nama, case=False, na=False)]
            # Tampilkan data
            st.subheader(f"Data Instansi ({len(filtered_df)} records)")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("Belum ada data instansi.")

    # Submenu Edit Instansi
    elif submenu == "✏️ Edit Instansi":
        st.subheader("Edit Instansi")
        df_instansi = read_instansi()
        if len(df_instansi) > 0:
            # Pilih instansi yang akan diedit
            instansi_list = df_instansi[['id', 'nama_instansi']].values.tolist()
            instansi_options = [f"{x[0]} - {x[1]}" for x in instansi_list]
            selected_instansi = st.selectbox("Pilih Instansi yang akan diedit:", instansi_options)
            if selected_instansi:
                instansi_id = int(selected_instansi.split(" - ")[0])
                instansi_data = get_instansi_by_id(instansi_id)
                if instansi_data:
                    with st.form("form_edit_instansi"):
                        nama_instansi = st.text_input("Nama Instansi*", value=instansi_data[1])
                        submitted = st.form_submit_button("Update Instansi")
                        if submitted:
                            if not nama_instansi:
                                st.error("Harap isi nama instansi.")
                            else:
                                update_instansi(instansi_id, nama_instansi)
                                st.success("Instansi berhasil diupdate!")
                                st.rerun()
        else:
            st.info("Belum ada data instansi untuk diedit.")

    # Submenu Hapus Instansi
    elif submenu == "🗑️ Hapus Instansi":
        st.subheader("Hapus Instansi")
        df_instansi = read_instansi()
        if len(df_instansi) > 0:
            # Pilih instansi yang akan dihapus
            instansi_list = df_instansi[['id', 'nama_instansi']].values.tolist()
            instansi_options = [f"{x[0]} - {x[1]}" for x in instansi_list]
            selected_instansi = st.selectbox("Pilih Instansi yang akan dihapus:", instansi_options)
            if selected_instansi:
                instansi_id = int(selected_instansi.split(" - ")[0])
                instansi_data = get_instansi_by_id(instansi_id)
                if instansi_data:
                    st.warning("⚠️ Data yang akan dihapus:")
                    st.write(f"**ID:** {instansi_data[0]}")
                    st.write(f"**Nama Instansi:** {instansi_data[1]}")
                    if st.button("Hapus Instansi", type="primary"):
                        delete_instansi(instansi_id)
                        st.success("Instansi berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada data instansi.")

# Halaman Kelola Penilai
elif menu == "👨‍🏫 Kelola Penilai":
    st.header("Kelola Data Penilai")
    submenu_penilai = st.sidebar.radio(
        "Pilih Submenu:",
        ["➕ Tambah Penilai", "👁️ Lihat Penilai", "✏️ Edit Penilai", "🗑️ Hapus Penilai"]
    )
    # Submenu Tambah Penilai
    if submenu_penilai == "➕ Tambah Penilai":
        st.subheader("Tambah Penilai Baru")
        # Select pangkat outside form for dynamic golongan update
        pangkat_penilai = st.selectbox("Pangkat", list(PANGKAT_OPTIONS.keys()), key='pangkat_tambah_penilai', on_change=update_golongan, args=('tambah_penilai',))
        with st.form("form_tambah_penilai"):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Lengkap*")
                nip = st.text_input("NIP*")
                no_seri_karpeg = st.text_input("No. Seri Karpeg")
                tempat_lahir = st.text_input("Tempat Lahir*")
                tanggal_lahir = st.date_input("Tanggal Lahir*", max_value=datetime.now())
                jenis_kelamin = st.selectbox("Jenis Kelamin*", ["Laki-laki", "Perempuan"])
            with col2:
                golongan = st.text_input("Golongan", value=st.session_state.get('golongan_tambah_penilai', ''), disabled=True)
                tmt_pangkat = st.date_input("TMT Pangkat")
                jabatan = st.text_input("Jabatan")
                tmt_jabatan = st.date_input("TMT Jabatan")
                unit_kerja = st.text_input("Unit Kerja")
            submitted = st.form_submit_button("Simpan Penilai")
            if submitted:
                if not nama or not nip or not tempat_lahir:
                    st.error("Harap isi field yang wajib diisi (*)")
                else:
                    data = (
                        nama, nip, no_seri_karpeg, tempat_lahir,
                        tanggal_lahir, jenis_kelamin, st.session_state['pangkat_tambah_penilai'], st.session_state.get('golongan_tambah_penilai', ''),
                        tmt_pangkat, jabatan, tmt_jabatan, unit_kerja
                    )
                    if create_penilai(data):
                        st.success("Data penilai berhasil disimpan!")
                    else:
                        st.error("NIP sudah terdaftar. Gunakan NIP yang berbeda.")

    # Submenu Lihat Penilai
    elif submenu_penilai == "👁️ Lihat Penilai":
        st.subheader("Data Penilai")
        df_penilai = read_penilai()
        if len(df_penilai) > 0:
            # Filter data
            st.subheader("Filter Data")
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_nama = st.text_input("Cari berdasarkan nama")
            with col2:
                filter_jabatan = st.text_input("Cari berdasarkan jabatan")
            with col3:
                filter_unit = st.text_input("Cari berdasarkan unit kerja")
            # Terapkan filter
            filtered_df = df_penilai.copy()
            if filter_nama:
                filtered_df = filtered_df[filtered_df['nama'].str.contains(filter_nama, case=False, na=False)]
            if filter_jabatan:
                filtered_df = filtered_df[filtered_df['jabatan'].str.contains(filter_jabatan, case=False, na=False)]
            if filter_unit:
                filtered_df = filtered_df[filtered_df['unit_kerja'].str.contains(filter_unit, case=False, na=False)]
            # Tampilkan data
            st.subheader(f"Data Penilai ({len(filtered_df)} records)")
            st.dataframe(filtered_df, use_container_width=True)
            # Ekspor data
            st.subheader("Ekspor Data")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ekspor ke CSV"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"data_penilai_{datetime.now().strftime('%d-%m-%Y')}.csv",
                        mime="text/csv"
                    )
            with col2:
                if st.button("Ekspor ke Excel"):
                    excel_file = filtered_df.to_excel("data_penilai.xlsx", index=False)
                    with open("data_penilai.xlsx", "rb") as file:
                        st.download_button(
                            label="Download Excel",
                            data=file,
                            file_name=f"data_penilai_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                            mime="application/vnd.ms-excel"
                        )

        else:
            st.info("Belum ada data penilai.")

    # Submenu Edit Penilai
    elif submenu_penilai == "✏️ Edit Penilai":
        st.subheader("Edit Data Penilai")
        df_penilai = read_penilai()
        if len(df_penilai) > 0:
            # Pilih penilai yang akan diedit
            penilai_list = df_penilai[['id', 'nama', 'nip']].values.tolist()
            penilai_options = [f"{x[0]} - {x[1]} (NIP: {x[2]})" for x in penilai_list]
            selected_penilai = st.selectbox("Pilih Penilai yang akan diedit:", penilai_options)
            if selected_penilai:
                penilai_id = int(selected_penilai.split(" - ")[0])
                penilai_data = get_penilai_by_id(penilai_id)
                if penilai_data:
                    with st.form("form_edit_penilai"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nama = st.text_input("Nama Lengkap*", value=penilai_data[1])
                            nip = st.text_input("NIP*", value=penilai_data[2])
                            no_seri_karpeg = st.text_input("No. Seri Karpeg", value=penilai_data[3] or "")
                            tempat_lahir = st.text_input("Tempat Lahir*", value=penilai_data[4])
                            tanggal_lahir = st.date_input("Tanggal Lahir*",
                                                        value=datetime.strptime(penilai_data[5], '%Y-%m-%d').date() if penilai_data[5] else datetime.now().date())
                            jenis_kelamin = st.selectbox("Jenis Kelamin*",
                                                       ["Laki-laki", "Perempuan"],
                                                       index=0 if penilai_data[6] == "Laki-laki" else 1)
                            pangkat = st.selectbox("Pangkat", list(PANGKAT_OPTIONS.keys()),
                                                 index=list(PANGKAT_OPTIONS.keys()).index(penilai_data[7]) if penilai_data[7] in PANGKAT_OPTIONS else 0)
                        with col2:
                            golongan = st.text_input("Golongan", value=PANGKAT_OPTIONS.get(pangkat, penilai_data[8] or ""), disabled=True)
                            tmt_pangkat = st.date_input("TMT Pangkat",
                                                      value=datetime.strptime(penilai_data[9], '%Y-%m-%d').date() if penilai_data[9] else datetime.now().date())
                            jabatan = st.text_input("Jabatan", value=penilai_data[10] or "")
                            tmt_jabatan = st.date_input("TMT Jabatan",
                                                      value=datetime.strptime(penilai_data[11], '%Y-%m-%d').date() if penilai_data[11] else datetime.now().date())
                            unit_kerja = st.text_input("Unit Kerja", value=penilai_data[12] or "")
                        submitted = st.form_submit_button("Update Data")
                        if submitted:
                            if not nama or not nip or not tempat_lahir:
                                st.error("Harap isi field yang wajib diisi (*)")
                            else:
                                data = (
                                    nama, nip, no_seri_karpeg, tempat_lahir,
                                    tanggal_lahir, jenis_kelamin, pangkat, golongan,
                                    tmt_pangkat, jabatan, tmt_jabatan, unit_kerja
                                )
                                update_penilai(penilai_id, data)
                                st.success("Data penilai berhasil diupdate!")
                                st.rerun()
        else:
            st.info("Belum ada data penilai untuk diedit.")

    # Submenu Hapus Penilai
    elif submenu_penilai == "🗑️ Hapus Penilai":
        st.subheader("Hapus Data Penilai")
        df_penilai = read_penilai()
        if len(df_penilai) > 0:
            # Pilih penilai yang akan dihapus
            penilai_list = df_penilai[['id', 'nama', 'nip']].values.tolist()
            penilai_options = [f"{x[0]} - {x[1]} (NIP: {x[2]})" for x in penilai_list]
            selected_penilai = st.selectbox("Pilih Penilai yang akan dihapus:", penilai_options)
            if selected_penilai:
                penilai_id = int(selected_penilai.split(" - ")[0])
                penilai_data = get_penilai_by_id(penilai_id)
                if penilai_data:
                    st.warning("⚠️ Data yang akan dihapus:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {penilai_data[0]}")
                        st.write(f"**Nama:** {penilai_data[1]}")
                        st.write(f"**NIP:** {penilai_data[2]}")
                        st.write(f"**Jabatan:** {penilai_data[10]}")
                    with col2:
                        st.write(f"**Unit Kerja:** {penilai_data[12]}")
                        st.write(f"**Pangkat:** {penilai_data[7]}")
                        st.write(f"**Golongan:** {penilai_data[8]}")
                    if st.button("Hapus Data", type="primary"):
                        delete_penilai(penilai_id)
                        st.success("Data penilai berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada data penilai.")

# Halaman Kelola Angka Integrasi
elif menu == "🔢 Kelola Angka Integrasi":
    st.header("Kelola Data Angka Integrasi")
    submenu_angka = st.sidebar.radio(
        "Pilih Submenu:",
        ["➕ Tambah Angka Integrasi", "👁️ Lihat Angka Integrasi", "✏️ Edit Angka Integrasi", "🗑️ Hapus Angka Integrasi"]
    )
    # Submenu Tambah Angka Integrasi
    if submenu_angka == "➕ Tambah Angka Integrasi":
        st.subheader("Tambah Angka Integrasi Baru")
        df_pegawai = get_pegawai_options()
        if len(df_pegawai) > 0:
            pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
            with st.form("form_tambah_angka_integrasi"):
                selected_pegawai = st.selectbox("Pilih Pegawai*", pegawai_options)
                jumlah_angka_integrasi = st.number_input("Jumlah Angka Integrasi*", min_value=0.0, step=0.01)
                submitted = st.form_submit_button("Simpan Angka Integrasi")
                if submitted:
                    if not selected_pegawai:
                        st.error("Harap pilih pegawai.")
                    elif jumlah_angka_integrasi <= 0:
                        st.error("Jumlah angka integrasi harus lebih dari 0.")
                    else:
                        pegawai_id = int(selected_pegawai.split(" - ")[0])
                        if create_angka_integrasi(pegawai_id, jumlah_angka_integrasi):
                            st.success("Angka integrasi berhasil ditambahkan!")
                        else:
                            st.error("Gagal menambahkan angka integrasi.")
        else:
            st.info("Belum ada data pegawai. Tambahkan pegawai terlebih dahulu.")

    # Submenu Lihat Angka Integrasi
    elif submenu_angka == "👁️ Lihat Angka Integrasi":
        st.subheader("Data Angka Integrasi")
        df_angka = read_angka_integrasi()
        if len(df_angka) > 0:
            # Filter data
            st.subheader("Filter Data")
            filter_nama = st.text_input("Cari berdasarkan nama pegawai")
            # Terapkan filter
            filtered_df = df_angka.copy()
            if filter_nama:
                filtered_df = filtered_df[filtered_df['nama'].str.contains(filter_nama, case=False, na=False)]
            # Tampilkan data
            st.subheader(f"Data Angka Integrasi ({len(filtered_df)} records)")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("Belum ada data angka integrasi.")

    # Submenu Edit Angka Integrasi
    elif submenu_angka == "✏️ Edit Angka Integrasi":
        st.subheader("Edit Angka Integrasi")
        df_angka = read_angka_integrasi()
        if len(df_angka) > 0:
            # Pilih angka integrasi yang akan diedit
            angka_list = df_angka[['id', 'nama', 'jumlah_angka_integrasi']].values.tolist()
            angka_options = [f"{x[0]} - {x[1]} (Jumlah: {x[2]})" for x in angka_list]
            selected_angka = st.selectbox("Pilih Angka Integrasi yang akan diedit:", angka_options)
            if selected_angka:
                angka_id = int(selected_angka.split(" - ")[0])
                angka_data = get_angka_integrasi_by_id(angka_id)
                df_pegawai = get_pegawai_options()
                pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
                if angka_data:
                    with st.form("form_edit_angka_integrasi"):
                        selected_pegawai = st.selectbox("Pilih Pegawai*", pegawai_options, index=[x['id'] for x in df_pegawai.to_dict('records')].index(angka_data[1]) if angka_data[1] in [x['id'] for x in df_pegawai.to_dict('records')] else 0)
                        jumlah_angka_integrasi = st.number_input("Jumlah Angka Integrasi*", min_value=0.0, step=0.01, value=float(angka_data[2]))
                        submitted = st.form_submit_button("Update Angka Integrasi")
                        if submitted:
                            if not selected_pegawai:
                                st.error("Harap pilih pegawai.")
                            elif jumlah_angka_integrasi <= 0:
                                st.error("Jumlah angka integrasi harus lebih dari 0.")
                            else:
                                pegawai_id = int(selected_pegawai.split(" - ")[0])
                                update_angka_integrasi(angka_id, pegawai_id, jumlah_angka_integrasi)
                                st.success("Angka integrasi berhasil diupdate!")
                                st.rerun()
        else:
            st.info("Belum ada data angka integrasi untuk diedit.")

    # Submenu Hapus Angka Integrasi
    elif submenu_angka == "🗑️ Hapus Angka Integrasi":
        st.subheader("Hapus Angka Integrasi")
        df_angka = read_angka_integrasi()
        if len(df_angka) > 0:
            # Pilih angka integrasi yang akan dihapus
            angka_list = df_angka[['id', 'nama', 'jumlah_angka_integrasi']].values.tolist()
            angka_options = [f"{x[0]} - {x[1]} (Jumlah: {x[2]})" for x in angka_list]
            selected_angka = st.selectbox("Pilih Angka Integrasi yang akan dihapus:", angka_options)
            if selected_angka:
                angka_id = int(selected_angka.split(" - ")[0])
                angka_data = get_angka_integrasi_by_id(angka_id)
                if angka_data:
                    st.warning("⚠️ Data yang akan dihapus:")
                    st.write(f"**ID:** {angka_data[0]}")
                    st.write(f"**Pegawai ID:** {angka_data[1]}")
                    st.write(f"**Jumlah Angka Integrasi:** {angka_data[2]}")
                    if st.button("Hapus Angka Integrasi", type="primary"):
                        delete_angka_integrasi(angka_id)
                        st.success("Angka integrasi berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada data angka integrasi.")

# Halaman Kelola AK
elif menu == "📋 Kelola AK":
    st.header("Kelola Data AK")
    submenu_ak = st.sidebar.radio(
        "Pilih Submenu:",
        ["➕ Tambah AK", "👁️ Lihat AK", "✏️ Edit AK", "🗑️ Hapus AK"]
    )
    # Submenu Tambah AK
    if submenu_ak == "➕ Tambah AK":
        st.subheader("Tambah AK Baru")
        df_pegawai = get_pegawai_options()
        df_instansi = get_instansi_options()
        df_penilai = get_penilai_options()
        if len(df_pegawai) > 0 and len(df_instansi) > 0 and len(df_penilai) > 0:
            pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
            instansi_options = df_instansi.apply(lambda x: f"{x['id']} - {x['nama_instansi']}", axis=1).tolist()
            penilai_options = df_penilai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
            penilaian = st.selectbox("Penilaian*", PENILAIAN_OPTIONS, key='penilaian_add')
            jenjang = st.selectbox("Jenjang*", JENJANG_OPTIONS, key='jenjang_add')

            # KONEKSI KE DB
            conn = sqlite3.connect('pegawai.db')
            # AMBIL DAFTAR PERIODE
            list_periode = get_unique_periods(conn)
            conn.close()

            tanggal_awal = datetime.now().replace(day=1).date()
            tanggal_akhir = datetime.now().date()
            if not list_periode:
                st.warning("Belum ada data periode AK yang tersimpan. Menggunakan tanggal saat ini sebagai default.")
            else:
                # BUAT SELECTBOX UNTUK MEMILIH PERIODE
                # options=[p[0] for p in list_periode] will display "DD-MM-YYYY s/d DD-MM-YYYY"
                # The actual value selected will be the display string, so we need to find the corresponding value string
                selected_display_str = st.selectbox(
                    "Pilih Periode Laporan",
                    options=[p[0] for p in list_periode],
                    index=0 # Pilih periode terbaru secara default (karena di-ORDER BY DESC)
                )
                # Find the corresponding value string (YYYY-MM-DD s/d YYYY-MM-DD)
                selected_value_str = next((p[1] for p in list_periode if p[0] == selected_display_str), None)

                if selected_value_str:
                    # PARSING PERIODE YANG DIPILIH KEMBALI MENJADI TANGGAL
                    start_date_str, end_date_str = selected_value_str.split(" s/d ")
                    # Konversi string tanggal kembali ke objek datetime.date
                    tanggal_awal = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    tanggal_akhir = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    # Tampilkan periode yang sedang aktif (opsional)
                    st.info(f"Memproses data untuk periode: **{tanggal_awal.strftime('%d-%m-%Y')}** s/d **{tanggal_akhir.strftime('%d-%m-%Y')}**")
                else:
                    st.warning("Tidak dapat menemukan periode yang dipilih. Menggunakan tanggal saat ini sebagai default.")

            # Now, the date inputs can be uncommented and pre-filled
            tanggal_awal = st.date_input("Tanggal Awal Penilaian*", value=tanggal_awal, key='tanggal_awal_add')
            tanggal_akhir = st.date_input("Tanggal Akhir Penilaian*", value=tanggal_akhir, key='tanggal_akhir_add')

            # Bagian yang perlu diupdate di ak.py, di dalam submenu "➕ Tambah AK"
            prosentase_value = PENILAIAN_TO_PROSENTASE.get(penilaian, 0)
            koefisien_value = JENJANG_TO_KOEFISIEN.get(jenjang, 0.0)

            if tanggal_awal and tanggal_akhir and tanggal_awal <= tanggal_akhir:
                # --- LOGIKA PERBAIKAN DIMULAI DI SINI ---
                # 1. Hitung total hari (termasuk tanggal akhir)
                total_days = (tanggal_akhir - tanggal_awal).days + 1
                # 2. Konversi hari ke durasi dalam tahun
                # Menggunakan 365.25 untuk mengakomodasi tahun kabisat (rata-rata tahun)
                duration_in_years = total_days / 365.25
                # 3. Hitung AK
                jumlah_angka_kredit_value = round(duration_in_years * koefisien_value * (prosentase_value / 100), 3) # Gunakan 3 angka di belakang koma untuk presisi
                # --- LOGIKA PERBAIKAN SELESAI DI SINI ---
            else:
                jumlah_angka_kredit_value = 0.0

            # Tambahkan pemeriksaan tambahan jika Anda curiga Prosentase atau Koefisien yang 0
            if prosentase_value == 0 or koefisien_value == 0.0:
                st.warning("Penilaian atau Jenjang yang dipilih mungkin tidak memiliki nilai Prosentase/Koefisien yang terdaftar.")
                jumlah_angka_kredit_value = 0.0

            st.write(f"Penilaian: {penilaian}")
            st.write(f"Jenjang: {jenjang}")
            st.write(f"Tanggal Awal: {tanggal_awal}")
            st.write(f"Tanggal Akhir: {tanggal_akhir}")
            st.write(f"Prosentase Value: {prosentase_value}")
            st.write(f"Koefisien Value: {koefisien_value}")
            st.write(f"Jumlah Angka Kredit Value: {jumlah_angka_kredit_value}") # Nilai yang ditampilkan ini harusnya sudah benar

            # Pastikan Anda mengubah pembulatan menjadi 3 desimal agar nilai kecil tidak dibulatkan menjadi nol
            # ...
            with st.form("form_tambah_ak"):
                col1, col2 = st.columns(2)
                with col1:
                    selected_pegawai = st.selectbox("Pilih Pegawai*", pegawai_options)
                    selected_instansi = st.selectbox("Pilih Instansi*", instansi_options)
                    selected_penilai = st.selectbox("Pilih Penilai*", penilai_options)
                    prosentase = st.number_input("Prosentase*", min_value=0, max_value=200, value=int(prosentase_value), disabled=True)
                    koefisien = st.number_input("Koefisien*", min_value=0.0, max_value=100.0, value=float(koefisien_value), disabled=True)
                    jumlah_angka_kredit = st.number_input("Jumlah Angka Kredit*", value=jumlah_angka_kredit_value, disabled=True)
                    tanggal_ditetapkan = st.date_input("Tanggal Ditetapkan*")
                    tempat_ditetapkan = st.text_input("Tempat Ditetapkan*")
                submitted = st.form_submit_button("Simpan AK")
                if submitted:
                    if not selected_pegawai or not selected_instansi or not selected_penilai or not penilaian or not tempat_ditetapkan or not jenjang:
                        st.error("Harap isi semua field yang wajib diisi (*)")
                    elif tanggal_awal > tanggal_akhir:
                        st.error("Tanggal awal penilaian tidak boleh lebih besar dari tanggal akhir penilaian.")
                    else:
                        pegawai_id = int(selected_pegawai.split(" - ")[0])
                        instansi_id = int(selected_instansi.split(" - ")[0])
                        penilai_id = int(selected_penilai.split(" - ")[0])
                        data = (
                            pegawai_id, instansi_id, penilai_id, tanggal_awal,
                            tanggal_akhir, penilaian, prosentase_value, koefisien_value, jumlah_angka_kredit_value, tanggal_ditetapkan, tempat_ditetapkan, jenjang
                        )
                        if create_ak(data):
                            st.success("AK berhasil ditambahkan!")
                        else:
                            st.error("Gagal menambahkan AK.")
        else:
            st.info("Pastikan ada data pegawai, instansi, dan penilai sebelum menambah AK.")

    # Submenu Lihat AK
    elif submenu_ak == "👁️ Lihat AK":
        st.subheader("Data AK")
        df_ak = read_ak()
        if len(df_ak) > 0:
            # Format kolom tanggal ke DD-MM-YYYY
            for col in ['tanggal_awal_penilaian', 'tanggal_akhir_penilaian', 'tanggal_ditetapkan']:
                if col in df_ak.columns:
                    df_ak[col] = pd.to_datetime(df_ak[col], dayfirst=True, errors='coerce').dt.strftime('%d-%m-%Y').fillna('')
            # Filter data
            st.subheader("Filter Data")
            filter_nama = st.text_input("Cari berdasarkan nama pegawai")
            # Terapkan filter
            filtered_df = df_ak.copy()
            if filter_nama:
                filtered_df = filtered_df[filtered_df['nama_pegawai'].str.contains(filter_nama, case=False, na=False)]
            # Tampilkan data
            st.subheader(f"Data AK ({len(filtered_df)} records)")
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("Belum ada data AK.")

    # Submenu Edit AK
    elif submenu_ak == "✏️ Edit AK":
        st.subheader("Edit AK")
        df_ak = read_ak()
        if len(df_ak) > 0:
            # Pilih AK yang akan diedit
            ak_list = df_ak[['id', 'nama_pegawai', 'nama_instansi']].values.tolist()
            ak_options = [f"{x[0]} - {x[1]} ({x[2]})" for x in ak_list]
            selected_ak = st.selectbox("Pilih AK yang akan diedit:", ak_options)
            if selected_ak:
                ak_id = int(selected_ak.split(" - ")[0])
                ak_data = get_ak_by_id(ak_id)
                df_pegawai = get_pegawai_options()
                df_instansi = get_instansi_options()
                df_penilai = get_penilai_options()
                pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
                instansi_options = df_instansi.apply(lambda x: f"{x['id']} - {x['nama_instansi']}", axis=1).tolist()
                penilai_options = df_penilai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
                if ak_data:
                    penilaian = st.selectbox("Penilaian*", PENILAIAN_OPTIONS, index=PENILAIAN_OPTIONS.index(ak_data[6]) if ak_data[6] in PENILAIAN_OPTIONS else 0, key='penilaian_edit')
                    jenjang = st.selectbox("Jenjang*", JENJANG_OPTIONS, index=JENJANG_OPTIONS.index(ak_data[12]) if ak_data[12] in JENJANG_OPTIONS else 0, key='jenjang_edit')
                    # tanggal_awal_edit = st.date_input("Tanggal Awal Penilaian*", value=datetime.strptime(ak_data[4], '%Y-%m-%d') if ak_data[4] else datetime.now().replace(day=1), key='tanggal_awal_edit')
                    # tanggal_akhir_edit = st.date_input("Tanggal Akhir Penilaian*", value=datetime.strptime(ak_data[5], '%Y-%m-%d') if ak_data[5] else datetime.now(), key='tanggal_akhir_edit')
            
                    # Helper untuk parsing tanggal dengan aman
                    def safe_parse_date(date_str, default_date):
                        if not date_str:
                            return default_date
                        try:
                            return datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            return default_date

                    tanggal_awal_edit = st.date_input(
                        "Tanggal Awal Penilaian*",
                        value=safe_parse_date(ak_data[4], datetime.now().replace(day=1).date()),
                        key='tanggal_awal_edit'
                    )
                    tanggal_akhir_edit = st.date_input(
                        "Tanggal Akhir Penilaian*",
                        value=safe_parse_date(ak_data[5], datetime.now().date()),
                        key='tanggal_akhir_edit'
                    )

                    prosentase_value = PENILAIAN_TO_PROSENTASE.get(penilaian, 0)
                    koefisien_value = JENJANG_TO_KOEFISIEN.get(jenjang, 0.0)
                    st.write(f"Penilaian (Edit): {penilaian}")
                    st.write(f"Jenjang (Edit): {jenjang}")
                    # st.write(f"Tanggal Awal (Edit): {tanggal_awal_edit}")
                    # st.write(f"Tanggal Akhir (Edit): {tanggal_akhir_edit}")
                    st.write(f"Tanggal Awal (Edit): {tanggal_awal_edit.strftime('%d-%m-%Y')}")
                    st.write(f"Tanggal Akhir (Edit): {tanggal_akhir_edit.strftime('%d-%m-%Y')}")
                    st.write(f"Prosentase Value (Edit): {prosentase_value}")
                    st.write(f"Koefisien Value (Edit): {koefisien_value}")

                    if tanggal_awal_edit and tanggal_akhir_edit and tanggal_awal_edit <= tanggal_akhir_edit:
                        # --- LOGIKA PERBAIKAN DIMULAI DI SINI (EDIT) ---
                        # 1. Hitung total hari (termasuk tanggal akhir)
                        total_days = (tanggal_akhir_edit - tanggal_awal_edit).days + 1
                        # 2. Konversi hari ke durasi dalam tahun
                        # Menggunakan 365.25 untuk mengakomodasi tahun kabisat (rata-rata tahun)
                        duration_in_years = total_days / 365.25
                        # 3. Hitung AK
                        jumlah_angka_kredit_value_edit = round(duration_in_years * koefisien_value * (prosentase_value / 100), 3) # Gunakan 3 angka di belakang koma untuk presisi
                        # --- LOGIKA PERBAIKAN SELESAI DI SINI (EDIT) ---
                    else:
                        jumlah_angka_kredit_value_edit = 0.0

                    st.write(f"Jumlah Angka Kredit Value (Edit): {jumlah_angka_kredit_value_edit}")

                    with st.form("form_edit_ak"):
                        col1, col2 = st.columns(2)
                        with col1:
                            selected_pegawai = st.selectbox("Pilih Pegawai*", pegawai_options, index=[i for i, s in enumerate(pegawai_options) if s.startswith(str(ak_data[1]))][0])
                            selected_instansi = st.selectbox("Pilih Instansi*", instansi_options, index=[i for i, s in enumerate(instansi_options) if s.startswith(str(ak_data[2]))][0])
                            selected_penilai = st.selectbox("Pilih Penilai*", penilai_options, index=[i for i, s in enumerate(penilai_options) if s.startswith(str(ak_data[3]))][0])
                            prosentase = st.number_input("Prosentase*", min_value=0, max_value=200, value=int(prosentase_value), disabled=True)
                            koefisien = st.number_input("Koefisien*", min_value=0.0, max_value=100.0, value=float(koefisien_value), disabled=True)
                            jumlah_angka_kredit = st.number_input("Jumlah Angka Kredit*", value=jumlah_angka_kredit_value_edit, disabled=True)
                            date_value_ditetapkan = datetime.now()
                            if ak_data[10] is not None:
                                if isinstance(ak_data[10], str):
                                    date_value_ditetapkan = datetime.strptime(ak_data[10], '%Y-%m-%d')
                                elif isinstance(ak_data[10], int):
                                    date_value_ditetapkan = datetime.fromtimestamp(ak_data[10])
                            tanggal_ditetapkan = st.date_input(
                            "Tanggal Ditetapkan*",
                            value=datetime.now().date(),  # atau datetime(2022, 1, 1).date() jika ingin selalu 2022
                            min_value=datetime(2022, 1, 1).date(),
                            max_value=datetime.now().date()
                            )
                            tempat_ditetapkan = st.text_input("Tempat Ditetapkan*", value=ak_data[11])
                        submitted = st.form_submit_button("Update AK")
                        if submitted:
                            if not selected_pegawai or not selected_instansi or not selected_penilai or not penilaian or not tempat_ditetapkan or not jenjang:
                                st.error("Harap isi semua field yang wajib diisi (*)")
                            elif tanggal_awal_edit > tanggal_akhir_edit:
                                st.error("Tanggal awal penilaian tidak boleh lebih besar dari tanggal akhir penilaian.")
                            else:
                                pegawai_id = int(selected_pegawai.split(" - ")[0])
                                instansi_id = int(selected_instansi.split(" - ")[0])
                                penilai_id = int(selected_penilai.split(" - ")[0])
                                data = (
                                    pegawai_id, instansi_id, penilai_id, tanggal_awal_edit,
                                    tanggal_akhir_edit, penilaian, prosentase_value, koefisien_value, jumlah_angka_kredit_value_edit, tanggal_ditetapkan, tempat_ditetapkan, jenjang
                                )
                                update_ak(ak_id, data)
                                st.success("AK berhasil diupdate!")
                                st.rerun()
        else:
            st.info("Belum ada data AK untuk diedit.")

    # Submenu Hapus AK
    elif submenu_ak == "🗑️ Hapus AK":
        st.subheader("Hapus AK")
        df_ak = read_ak()
        if len(df_ak) > 0:
            # Pilih AK yang akan dihapus
            ak_list = df_ak[['id', 'nama_pegawai', 'nama_instansi']].values.tolist()
            ak_options = [f"{x[0]} - {x[1]} ({x[2]})" for x in ak_list]
            selected_ak = st.selectbox("Pilih AK yang akan dihapus:", ak_options)
            if selected_ak:
                ak_id = int(selected_ak.split(" - ")[0])
                ak_data = get_ak_by_id(ak_id)
                if ak_data:
                    st.warning("⚠️ Data yang akan dihapus:")
                    st.write(f"**ID:** {ak_data[0]}")
                    st.write(f"**Pegawai ID:** {ak_data[1]}")
                    st.write(f"**Instansi ID:** {ak_data[2]}")
                    st.write(f"**Penilai ID:** {ak_data[3]}")
                    st.write(f"**Tanggal Awal Penilaian:** {ak_data[4]}")
                    st.write(f"**Tanggal Akhir Penilaian:** {ak_data[5]}")
                    st.write(f"**Penilaian:** {ak_data[6]}")
                    st.write(f"**Prosentase:** {ak_data[7]}") # Indeks 7 adalah prosentase
                    st.write(f"**Koefisien:** {ak_data[8]}") # Indeks 8 adalah koefisien
                    st.write(f"**Jumlah Angka Kredit:** {ak_data[9]}") # Indeks 9 adalah jumlah_angka_kredit
                    st.write(f"**Tanggal Ditetapkan:** {ak_data[10]}")
                    st.write(f"**Tempat Ditetapkan:** {ak_data[11]}")
                    st.write(f"**Jenjang:** {ak_data[12]}")
                    if st.button("Hapus AK", type="primary"):
                        delete_ak(ak_id)
                        st.success("AK berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada data AK.")

# Halaman Laporan
elif menu == "📊 Laporan":
    st.header("📊 Laporan Angka Kredit")
    # Pilih jenis laporan
    jenis_laporan = st.selectbox(
        "Pilih Jenis Laporan:",
        ["Penetapan", "Akumulasi", "Konversi"]
    )
    # Pilih pegawai
    df_pegawai = get_pegawai_options()
    if len(df_pegawai) > 0:
        pegawai_options = df_pegawai.apply(lambda x: f"{x['id']} - {x['nama']} (NIP: {x['nip']})", axis=1).tolist()
        selected_pegawai = st.selectbox("Pilih Pegawai:", pegawai_options)
        if selected_pegawai:
            pegawai_id = int(selected_pegawai.split(" - ")[0])
            
            # --- FILTER PERIODE DINAMIS SESUAI CHECKED ITEMS ---
            st.subheader("Pilih Periode Laporan")
            conn = sqlite3.connect('pegawai.db')
            list_periode_tuple = get_unique_periods(conn)
            conn.close()

            if not list_periode_tuple:
                st.warning("Belum ada data periode AK yang tersimpan di database. Silakan tambah data AK terlebih dahulu.")
            else:
                # Pisahkan label tampilan dan value
                period_labels = [item[0] for item in list_periode_tuple]  # Format: "DD-MM-YYYY s/d DD-MM-YYYY"
                period_values = [item[1] for item in list_periode_tuple]  # Format: "YYYY-MM-DD s/d YYYY-MM-DD"

                # Tentukan apakah perlu tampilkan opsi "Angka Integrasi"
                include_ai_option = jenis_laporan in ["Penetapan", "Konversi", "Akumulasi"]
                options = period_labels + (["Angka Integrasi"] if include_ai_option else [])
                selected_labels = st.multiselect(
                    "Pilih Periode (dan/atau Angka Integrasi)",
                    options=options,
                    default=[period_labels[0]]  # Default: periode terbaru
                )

                include_angka_integrasi = "Angka Integrasi" in selected_labels
                selected_period_labels = [lbl for lbl in selected_labels if lbl != "Angka Integrasi"]

                # Ambil data AK hanya untuk periode yang dipilih
                df_ak = pd.DataFrame()
                if selected_period_labels:
                    # Bangun daftar pasangan (tgl_awal, tgl_akhir) dari pilihan
                    selected_periods = []
                    for lbl in selected_period_labels:
                        idx = period_labels.index(lbl)
                        start_str, end_str = period_values[idx].split(" s/d ")
                        selected_periods.append((start_str, end_str))

                    # Ambil data AK yang MATCH persis dengan pasangan tersebut
                    conditions = " OR ".join(
                        "(ak.tanggal_awal_penilaian = ? AND ak.tanggal_akhir_penilaian = ?)"
                        for _ in selected_periods
                    )
                    params = [pegawai_id]
                    for tgl_awal, tgl_akhir in selected_periods:
                        params.extend([tgl_awal, tgl_akhir])

                    conn = get_connection()
                    query = f'''
                        SELECT 
                            p.nama as nama_pegawai,
                            p.nip,
                            p.no_seri_karpeg,
                            p.tempat_lahir,
                            p.tanggal_lahir,
                            p.jenis_kelamin,
                            p.pangkat,
                            p.golongan,
                            p.tmt_pangkat,
                            p.jabatan,
                            p.tmt_jabatan,
                            p.unit_kerja,
                            i.nama_instansi,
                            pen.nama as nama_penilai,
                            pen.nip as nip_penilai,
                            ak.tanggal_awal_penilaian,
                            ak.tanggal_akhir_penilaian,
                            ak.penilaian,
                            ak.prosentase,
                            ak.koefisien,
                            ak.jumlah_angka_kredit,
                            ak.tanggal_ditetapkan,
                            ak.tempat_ditetapkan,
                            ak.jenjang
                        FROM ak
                        JOIN pegawai p ON ak.pegawai_id = p.id
                        JOIN instansi i ON ak.instansi_id = i.id
                        JOIN penilai pen ON ak.penilai_id = pen.id
                        WHERE p.id = ? AND ({conditions})
                    '''
                    df_ak = pd.read_sql(query, conn, params=params)
                    conn.close()

                # Ambil angka integrasi jika diperlukan
                angka_integrasi_value = 0.0
                if include_angka_integrasi:
                    df_ai = get_angka_integrasi_for_report(pegawai_id)
                    if not df_ai.empty:
                        angka_integrasi_value = df_ai['jumlah_angka_integrasi'].iloc[0]

                # Ambil data pegawai lengkap (dengan instansi & penilai jika tersedia)
                data_pegawai = get_pegawai_data_for_report(pegawai_id)
                if not data_pegawai:
                    st.error("Data pegawai tidak ditemukan.")
                    st.stop()

                # Generate laporan
                html_report = ""
                if jenis_laporan == "Penetapan":
                    html_report = generate_penetapan_html(
                        data_pegawai,
                        df_ak,
                        include_angka_integrasi=include_angka_integrasi,
                        angka_integrasi_value=angka_integrasi_value
                    )
                elif jenis_laporan == "Akumulasi":
                    html_report = generate_akumulasi_html(
                        data_pegawai,
                        df_ak,
                        include_angka_integrasi=include_angka_integrasi,
                        angka_integrasi_value=angka_integrasi_value
                    )
                elif jenis_laporan == "Konversi":
                    html_report = generate_konversi_html(
                        data_pegawai,
                        df_ak,
                        include_angka_integrasi=include_angka_integrasi,
                        angka_integrasi_value=angka_integrasi_value
                    )

                if html_report:
                    st.subheader("Preview Laporan")
                    st.components.v1.html(html_report, height=800, scrolling=True)

                    # Tombol Cetak
                    st.components.v1.html(
                        f"""
                        <script>
                            function printReport() {{
                                const printWindow = window.open('', '_blank');
                                printWindow.document.write(`
                                    {html_report.replace('`', '\\`')}
                                `);
                                printWindow.document.close();
                                printWindow.focus();
                                printWindow.print();
                                printWindow.close();
                            }}
                        </script>
                        <button onclick="printReport()" style="
                            background-color: #4CAF50;
                            color: white;
                            padding: 10px 20px;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                            margin-top: 10px;
                        ">
                            🖨️ Cetak Laporan
                        </button>
                        """,
                        height=80
                    )

                    # Tombol Download PDF for all report types
                    # Extract employee name and dates for the filename
                    nama_pegawai = data_pegawai.get('nama_pegawai', 'pegawai')

                    # Extract dates from the data
                    if not df_ak.empty and 'tanggal_awal_penilaian' in df_ak.columns:
                        tanggal_awal = pd.to_datetime(df_ak['tanggal_awal_penilaian'].min()).strftime('%d-%m-%Y')
                        tanggal_akhir = pd.to_datetime(df_ak['tanggal_akhir_penilaian'].max()).strftime('%d-%m-%Y')
                    else:
                        tanggal_awal = "01-01-2024"
                        tanggal_akhir = "31-12-2024"

                    # Determine the report type for the filename
                    if jenis_laporan == "Penetapan":
                        report_prefix = "Penetapan"
                    elif jenis_laporan == "Akumulasi":
                        report_prefix = "Akumulasi"
                    else:  # Konversi
                        report_prefix = "Konversi"

                    # Generate PDF
                    pdf_bytes = html_to_pdf_with_weasyprint(html_report, nama_pegawai, tanggal_awal, tanggal_akhir)

                    # Create download button with custom naming
                    filename = f"{report_prefix} an.{nama_pegawai} periode {tanggal_awal} s.d {tanggal_akhir}.pdf"
                    st.download_button(
                        label=f"📥 Download PDF {jenis_laporan}",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf"
                    )
    else:
        st.info("Belum ada data pegawai. Silakan tambahkan data pegawai terlebih dahulu.")