from django.contrib import admin
from .models import Pegawai, Instansi, Penilai, AngkaIntegrasi, AK

@admin.register(Pegawai)
class PegawaiAdmin(admin.ModelAdmin):
    list_display = ('nama', 'nip', 'pangkat', 'golongan', 'jabatan', 'unit_kerja')
    list_filter = ('pangkat', 'golongan', 'unit_kerja', 'jenis_kelamin')
    search_fields = ('nama', 'nip', 'no_seri_karpeg')
    ordering = ('nama',)

@admin.register(Instansi)
class InstansiAdmin(admin.ModelAdmin):
    list_display = ('nama_instansi',)
    search_fields = ('nama_instansi',)

@admin.register(Penilai)
class PenilaiAdmin(admin.ModelAdmin):
    list_display = ('nama', 'nip', 'pangkat', 'golongan', 'jabatan', 'unit_kerja')
    list_filter = ('pangkat', 'golongan', 'unit_kerja', 'jenis_kelamin')
    search_fields = ('nama', 'nip', 'no_seri_karpeg')
    ordering = ('nama',)

@admin.register(AngkaIntegrasi)
class AngkaIntegrasiAdmin(admin.ModelAdmin):
    list_display = ('pegawai', 'jumlah_angka_integrasi')
    search_fields = ('pegawai__nama', 'pegawai__nip')

@admin.register(AK)
class AKAdmin(admin.ModelAdmin):
    list_display = ('pegawai', 'tanggal_awal_penilaian', 'tanggal_akhir_penilaian', 'jumlah_angka_kredit', 'jenjang')
    list_filter = ('jenjang', 'penilaian', 'instansi', 'penilai')
    search_fields = ('pegawai__nama', 'pegawai__nip', 'instansi__nama_instansi', 'penilai__nama')
    ordering = ('pegawai', 'tanggal_awal_penilaian')
