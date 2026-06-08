"""
generate_license.py — Dijalankan admin untuk membuat license.key dari HWID.

Penggunaan:
    python generate_license.py <HWID>

Contoh:
    python generate_license.py A3F2B1C8D4E5F6A7B8C9D0E1F2A3B4C5

File license.key yang dihasilkan dikirim ke pengguna untuk dicopy
ke folder AppAK (sejajar dengan AppAK.exe).
"""
import sys
import hmac
import hashlib

SECRET = b"AppAK-LicenseSecret-2026"  # Ganti dengan secret Anda sendiri


def generate_license(hwid: str) -> str:
    hwid = hwid.strip().upper()
    sig = hmac.new(SECRET, hwid.encode(), hashlib.sha256).hexdigest().upper()
    return f"{hwid}:{sig}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_license.py <HWID>")
        sys.exit(1)

    hwid = sys.argv[1]
    license_content = generate_license(hwid)

    with open("license.key", "w") as f:
        f.write(license_content)

    print(f"license.key dibuat untuk HWID: {hwid}")
    print(f"Kirimkan file license.key ke pengguna.")
