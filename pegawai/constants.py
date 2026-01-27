# pegawai/constants.py

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

PENGURANGAN_GOLONGAN = {
    "III/a": 0,
    "III/b": 50,
    "III/c": 0,
    "III/d": 100,
}

# Data penilaian options
PENILAIAN_OPTIONS = [
    "Sangat Baik",
    "Baik",
    "Butuh Perbaikan",
    "Kurang",
    "Sangat Kurang"
]
