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

    def __str__(self):
        return f"{self.pegawai.nama} - {self.jenis_kegiatan} ({self.tanggal_pelaksanaan})"