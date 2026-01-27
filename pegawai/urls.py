from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('list/', views.pegawai_list, name='pegawai_list'),
    path('new/', views.PegawaiCreateView.as_view(), name='pegawai_new'),
    path('edit/<int:pk>/', views.PegawaiUpdateView.as_view(), name='pegawai_edit'),
    path('delete/<int:pk>/', views.PegawaiDeleteView.as_view(), name='pegawai_delete'),

    # Export and Import URLs
    path('export/', views.export_pegawai_csv, name='pegawai_export'),
    path('import/', views.import_pegawai_csv, name='pegawai_import'),
    path('export-import/', views.pegawai_export_import, name='pegawai_export_import'),

    path('konversi/', views.konversi_view, name='konversi'),
    path('konversi/pdf/', views.konversi_pdf_view, name='konversi_pdf'),

    path('akumulasi/', views.akumulasi_view, name='akumulasi'),
    path('akumulasi/pdf/', views.akumulasi_pdf_view, name='akumulasi_pdf'),

    path('penetapan/', views.penetapan_view, name='penetapan'),
    path('penetapan/pdf/', views.penetapan_pdf_view, name='penetapan_pdf'),

    path('merge_report/', views.merge_report_view, name='merge_report'),
    path('merge_report/pdf/', views.merge_report_pdf_view, name='merge_report_pdf'),

    path('angka_integrasi/', views.angka_integrasi_list, name='angka_integrasi_list'),
    path('angka_integrasi/new/', views.AngkaIntegrasiCreateView.as_view(), name='angka_integrasi_new'),
    path('angka_integrasi/edit/<int:pk>/', views.AngkaIntegrasiUpdateView.as_view(), name='angka_integrasi_edit'),
    path('angka_integrasi/delete/<int:pk>/', views.AngkaIntegrasiDeleteView.as_view(), name='angka_integrasi_delete'),

    path('instansi/', views.instansi_list, name='instansi_list'),
    path('instansi/new/', views.InstansiCreateView.as_view(), name='instansi_new'),
    path('instansi/edit/<int:pk>/', views.InstansiUpdateView.as_view(), name='instansi_edit'),
    path('instansi/delete/<int:pk>/', views.InstansiDeleteView.as_view(), name='instansi_delete'),

    path('penilai/', views.penilai_list, name='penilai_list'),
    path('penilai/new/', views.PenilaiCreateView.as_view(), name='penilai_new'),
    path('penilai/edit/<int:pk>/', views.PenilaiUpdateView.as_view(), name='penilai_edit'),
    path('penilai/delete/<int:pk>/', views.PenilaiDeleteView.as_view(), name='penilai_delete'),

    path('ak/', views.ak_list, name='ak_list'),
    path('ak/new/', views.AKCreateView.as_view(), name='ak_new'),
    path('ak/edit/<int:pk>/', views.AKUpdateView.as_view(), name='ak_edit'),
    path('ak/delete/<int:pk>/', views.AKDeleteView.as_view(), name='ak_delete'),

    # Instruction manual
    path('manual/', views.instruction_manual_pdf, name='instruction_manual'),

]