from django.db import models

class Pegawai(models.Model):
    nama = models.CharField(max_length=255)
    nip = models.CharField(max_length=255, unique=True)
    no_seri_karpeg = models.CharField(max_length=255, blank=True, null=True)
    tempat_lahir = models.CharField(max_length=255)
    tanggal_lahir = models.DateField()
    jenis_kelamin = models.CharField(max_length=20)
    pangkat = models.CharField(max_length=255)
    golongan = models.CharField(max_length=255)
    tmt_pangkat = models.DateField()
    jabatan = models.CharField(max_length=255)
    tmt_jabatan = models.DateField()
    unit_kerja = models.CharField(max_length=255)

    def __str__(self):
        return self.nama

class Instansi(models.Model):
    nama_instansi = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nama_instansi

class Penilai(models.Model):
    nama = models.CharField(max_length=255)
    nip = models.CharField(max_length=255, unique=True)
    no_seri_karpeg = models.CharField(max_length=255, blank=True, null=True)
    tempat_lahir = models.CharField(max_length=255)
    tanggal_lahir = models.DateField()
    jenis_kelamin = models.CharField(max_length=20)
    pangkat = models.CharField(max_length=255)
    golongan = models.CharField(max_length=255)
    tmt_pangkat = models.DateField()
    jabatan = models.CharField(max_length=255)
    tmt_jabatan = models.DateField()
    unit_kerja = models.CharField(max_length=255)

    def __str__(self):
        return self.nama


class AngkaIntegrasi(models.Model):
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE)
    jumlah_angka_integrasi = models.FloatField()

    def __str__(self):
        return f"{self.pegawai.nama} - {self.jumlah_angka_integrasi}"

class AK(models.Model):
    
    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE)
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE)
    penilai = models.ForeignKey(Penilai, on_delete=models.CASCADE)
    tanggal_awal_penilaian = models.DateField()
    tanggal_akhir_penilaian = models.DateField()
    penilaian = models.CharField(max_length=255)
    prosentase = models.IntegerField()
    koefisien = models.FloatField()
    jumlah_angka_kredit = models.FloatField()
    tanggal_ditetapkan = models.DateField()
    tempat_ditetapkan = models.CharField(max_length=255)
    jenjang = models.CharField(max_length=255)
    # jumlah_angka_kredit = models.DecimalField(
    #     max_digits=10,
    #     decimal_places=3,
    #     null=True,
    #     blank=True
    # )

    def __str__(self):
        return f"{self.pegawai.nama} - {self.tanggal_awal_penilaian} to {self.tanggal_akhir_penilaian}"


class AkPendidikan(models.Model):
    """Model for Educational Credit Points (Angka Kredit Pendidikan)"""

    pegawai = models.ForeignKey(Pegawai, on_delete=models.CASCADE, verbose_name="Pegawai")
    instansi = models.ForeignKey(Instansi, on_delete=models.CASCADE, verbose_name="Instansi")
    penilai = models.ForeignKey(Penilai, on_delete=models.CASCADE, verbose_name="Penilai")
    tanggal_awal_penilaian = models.DateField(verbose_name="Tanggal Awal Penilaian")
    tanggal_akhir_penilaian = models.DateField(verbose_name="Tanggal Akhir Penilaian")
    jenis_kegiatan = models.CharField(max_length=255, verbose_name="Jenis Kegiatan Pendidikan")
    tingkat = models.CharField(max_length=255, verbose_name="Tingkat Pendidikan", blank=True, null=True)
    tanggal_pelaksanaan = models.DateField(verbose_name="Tanggal Pelaksanaan")
    durasi_pelatihan = models.IntegerField(verbose_name="Durasi Pelatihan (Jam)", help_text="Durasi pelatihan dalam jam")
    jumlah_angka_kredit = models.FloatField(verbose_name="Jumlah Angka Kredit")
    tanggal_ditetapkan = models.DateField(verbose_name="Tanggal Ditentukan")
    tempat_ditetapkan = models.CharField(max_length=255, verbose_name="Tempat Ditentukan")
    nomor_sertifikat = models.CharField(max_length=255, verbose_name="Nomor Sertifikat", unique=True)
    file_sertifikat = models.FileField(upload_to='sertifikat_pendidikan/', verbose_name="File Sertifikat", blank=True, null=True)

    def save(self, *args, **kwargs):
        # Only auto-calculate jumlah_angka_kredit if it's not already set (0 or None)
        if not self.jumlah_angka_kredit or self.jumlah_angka_kredit == 0:
            # Calculate jumlah_angka_kredit as 25% of the minimal credit required for promotion
            # based on the employee's current rank
            from .constants import MINIMAL_AK_MAPPING, GOLONGAN_HIERARKI, PANGKAT_OPTIONS

            try:
                # Get the employee's current rank/golongan
                current_golongan = self.pegawai.golongan

                # Find the next rank for this employee
                if current_golongan in GOLONGAN_HIERARKI:
                    current_idx = GOLONGAN_HIERARKI.index(current_golongan)
                    if current_idx < len(GOLONGAN_HIERARKI) - 1:
                        next_golongan = GOLONGAN_HIERARKI[current_idx + 1]

                        # Look up the minimal credit required for promotion
                        key = (current_golongan, next_golongan)
                        if key in MINIMAL_AK_MAPPING:
                            pangkat_minimal, jenjang_minimal = MINIMAL_AK_MAPPING[key]

                            # Use the higher of the two values for calculation
                            minimal_credit = max(pangkat_minimal, jenjang_minimal) if jenjang_minimal is not None else pangkat_minimal

                            # Calculate 25% of the minimal credit required for promotion
                            self.jumlah_angka_kredit = minimal_credit * 0.25
                        else:
                            # If no mapping exists, set a default value or leave as 0
                            self.jumlah_angka_kredit = 0.0
                    else:
                        # Employee is at the highest rank
                        self.jumlah_angka_kredit = 0.0
                else:
                    # Current golongan not in hierarchy, set default
                    self.jumlah_angka_kredit = 0.0
            except Exception as e:
                # In case of any error, set to 0 to allow manual entry
                self.jumlah_angka_kredit = 0.0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pegawai.nama} - {self.jenis_kegiatan} ({self.tanggal_pelaksanaan})"