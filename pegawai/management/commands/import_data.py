import sqlite3
import pandas as pd
from django.core.management.base import BaseCommand
from pegawai.models import Pegawai, Instansi, Penilai, AngkaIntegrasi, AK

class Command(BaseCommand):
    help = 'Import data from old pegawai.db'

    def handle(self, *args, **options):
        conn = sqlite3.connect('pegawai.db')

        # Clear existing data
        self.stdout.write('Clearing existing data...')
        AK.objects.all().delete()
        AngkaIntegrasi.objects.all().delete()
        Penilai.objects.all().delete()
        Pegawai.objects.all().delete()
        Instansi.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared existing data.'))

        # Import Instansi
        self.stdout.write('Importing Instansi...')
        df_instansi = pd.read_sql('SELECT * FROM instansi', conn)
        instansi_map = {}
        for _, row in df_instansi.iterrows():
            instansi = Instansi.objects.create(
                nama_instansi=row['nama_instansi']
            )
            instansi_map[row['id']] = instansi
        self.stdout.write(self.style.SUCCESS('Successfully imported Instansi.'))

        # Import Pegawai
        self.stdout.write('Importing Pegawai...')
        df_pegawai = pd.read_sql('SELECT * FROM pegawai', conn)
        pegawai_map = {}
        for _, row in df_pegawai.iterrows():
            pegawai = Pegawai.objects.create(
                nama=row['nama'],
                nip=row['nip'],
                no_seri_karpeg=row['no_seri_karpeg'],
                tempat_lahir=row['tempat_lahir'],
                tanggal_lahir=row['tanggal_lahir'],
                jenis_kelamin=row['jenis_kelamin'],
                pangkat=row['pangkat'],
                golongan=row['golongan'],
                tmt_pangkat=row['tmt_pangkat'],
                jabatan=row['jabatan'],
                tmt_jabatan=row['tmt_jabatan'],
                unit_kerja=row['unit_kerja'],
            )
            pegawai_map[row['id']] = pegawai
        self.stdout.write(self.style.SUCCESS('Successfully imported Pegawai.'))

        # Import Penilai
        self.stdout.write('Importing Penilai...')
        df_penilai = pd.read_sql('SELECT * FROM penilai', conn)
        penilai_map = {}
        for _, row in df_penilai.iterrows():
            penilai = Penilai.objects.create(
                nama=row['nama'],
                nip=row['nip'],
                no_seri_karpeg=row['no_seri_karpeg'],
                tempat_lahir=row['tempat_lahir'],
                tanggal_lahir=row['tanggal_lahir'],
                jenis_kelamin=row['jenis_kelamin'],
                pangkat=row['pangkat'],
                golongan=row['golongan'],
                tmt_pangkat=row['tmt_pangkat'],
                jabatan=row['jabatan'],
                tmt_jabatan=row['tmt_jabatan'],
                unit_kerja=row['unit_kerja'],
            )
            penilai_map[row['id']] = penilai
        self.stdout.write(self.style.SUCCESS('Successfully imported Penilai.'))

        # Import AngkaIntegrasi
        self.stdout.write('Importing AngkaIntegrasi...')
        df_angka_integrasi = pd.read_sql('SELECT * FROM angka_integrasi', conn)
        for _, row in df_angka_integrasi.iterrows():
            pegawai = pegawai_map.get(row['pegawai_id'])
            if pegawai:
                AngkaIntegrasi.objects.create(
                    pegawai=pegawai,
                    jumlah_angka_integrasi=row['jumlah_angka_integrasi'],
                )
        self.stdout.write(self.style.SUCCESS('Successfully imported AngkaIntegrasi.'))

        # Import AK
        self.stdout.write('Importing AK...')
        df_ak = pd.read_sql('SELECT * FROM ak', conn)
        for _, row in df_ak.iterrows():
            pegawai = pegawai_map.get(row['pegawai_id'])
            instansi = instansi_map.get(row['instansi_id'])
            penilai = penilai_map.get(row['penilai_id'])
            if pegawai and instansi and penilai:
                AK.objects.create(
                    pegawai=pegawai,
                    instansi=instansi,
                    penilai=penilai,
                    tanggal_awal_penilaian=row['tanggal_awal_penilaian'],
                    tanggal_akhir_penilaian=row['tanggal_akhir_penilaian'],
                    penilaian=row['penilaian'],
                    prosentase=row['prosentase'],
                    koefisien=row['koefisien'],
                    jumlah_angka_kredit=row['jumlah_angka_kredit'],
                    tanggal_ditetapkan=row['tanggal_ditetapkan'],
                    tempat_ditetapkan=row['tempat_ditetapkan'],
                    jenjang=row['jenjang'],
                )
        self.stdout.write(self.style.SUCCESS('Successfully imported AK.'))

        conn.close()