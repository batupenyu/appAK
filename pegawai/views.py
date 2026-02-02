import csv
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import Pegawai, AngkaIntegrasi, Instansi, Penilai, AK, AkPendidikan
from .forms import AKForm, PegawaiForm, AngkaIntegrasiForm, InstansiForm, PenilaiForm, AkPendidikanForm
from datetime import datetime
from django.db import models
from dateutil.relativedelta import relativedelta
from .utils import render_to_pdf, export_pegawai_to_csv, import_pegawai_from_csv
from django.conf import settings
# pegawai/views.py
from django.http import HttpResponse

from .constants import (
    PANGKAT_OPTIONS, GOLONGAN_HIERARKI, JENJANG_OPTIONS,
    PENILAIAN_TO_PROSENTASE, JENJANG_TO_KOEFISIEN, MINIMAL_AK_MAPPING,
    GOLONGAN_TO_LAMA
)


def debug_base(request):
    """Test jika base.html berfungsi"""
    return render(request, 'pegawai/base.html', {'title': 'Test Page'})

def debug_simple(request):
    """Test template sederhana"""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
    <h1>Test Berhasil</h1>
    <p>Jika ini muncul, server Django berjalan normal.</p>
    </body>
    </html>
    """
    return HttpResponse(html)

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

def _calculate_ak_fields(ak_instance):
    """Calculates and sets prosentase, koefisien, and jumlah_angka_kredit for an AK instance."""
    
    # Calculate prosentase
    prosentase = PENILAIAN_TO_PROSENTASE.get(ak_instance.penilaian, 0)
    ak_instance.prosentase = prosentase

    # Calculate koefisien
    koefisien = JENJANG_TO_KOEFISIEN.get(ak_instance.jenjang, 0.0)
    ak_instance.koefisien = koefisien

    # Calculate month count
    month_count = 0
    if ak_instance.tanggal_awal_penilaian and ak_instance.tanggal_akhir_penilaian:
        delta = relativedelta(ak_instance.tanggal_akhir_penilaian, ak_instance.tanggal_awal_penilaian)
        month_count = delta.years * 12 + delta.months
        if delta.days > 0: # Include partial month if days exist
            month_count += 1
        if month_count == 0 and ak_instance.tanggal_awal_penilaian < ak_instance.tanggal_akhir_penilaian: # Ensure at least 1 month if dates are valid
            month_count = 1

    # Calculate jumlah_angka_kredit
    # Formula: (month_count / 12) * koefisien * (prosentase / 100)
    jumlah_angka_kredit = (month_count / 12) * koefisien * (prosentase / 100)
    ak_instance.jumlah_angka_kredit = jumlah_angka_kredit

    return ak_instance


def dashboard(request):
    total_pegawai = Pegawai.objects.count()
    total_instansi = Instansi.objects.count()
    total_penilai = Penilai.objects.count()
    total_ak = AK.objects.count()
    context = {
        'total_pegawai': total_pegawai,
        'total_instansi': total_instansi,
        'total_penilai': total_penilai,
        'total_ak': total_ak,
    }
    return render(request, 'pegawai/dashboard.html', context)

from django.core.paginator import Paginator

def pegawai_list(request):
    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # Start with all Pegawai objects, ordered by name in ascending order
    pegawai_list = Pegawai.objects.order_by('nama')

    # If there's a search query, filter by employee name
    if search_query:
        pegawai_list = pegawai_list.filter(nama__icontains=search_query)

    # Apply pagination
    paginator = Paginator(pegawai_list, 5)  # Show 5 employees per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pegawai/pegawai_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

class PegawaiCreateView(CreateView):
    model = Pegawai
    form_class = PegawaiForm
    template_name = 'pegawai/pegawai_form.html'
    success_url = reverse_lazy('pegawai_list')

class PegawaiUpdateView(UpdateView):
    model = Pegawai
    form_class = PegawaiForm
    template_name = 'pegawai/pegawai_form.html'
    success_url = reverse_lazy('pegawai_list')

class PegawaiDeleteView(DeleteView):
    model = Pegawai
    template_name = 'pegawai/pegawai_confirm_delete.html'
    success_url = reverse_lazy('pegawai_list')


def export_pegawai_csv(request):
    """Export all Pegawai data to CSV file."""
    csv_content = export_pegawai_to_csv()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pegawai_data.csv"'
    return response

def import_pegawai_csv(request):
    """Import Pegawai data from CSV file."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        # Validate file type
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File harus berupa file CSV.')
            return JsonResponse({'success': False, 'error': 'File harus berupa file CSV.'})

        try:
            imported_count, errors = import_pegawai_from_csv(csv_file)

            if errors:
                messages.warning(request, f'Berhasil mengimpor {imported_count} data. Ada {len(errors)} kesalahan.')
                return JsonResponse({
                    'success': True,
                    'imported_count': imported_count,
                    'errors': errors
                })
            else:
                messages.success(request, f'Berhasil mengimpor {imported_count} data Pegawai.')
                return JsonResponse({
                    'success': True,
                    'imported_count': imported_count,
                    'errors': []
                })

        except Exception as e:
            error_msg = f'Gagal mengimpor file: {str(e)}'
            messages.error(request, error_msg)
            return JsonResponse({'success': False, 'error': error_msg})

    return JsonResponse({'success': False, 'error': 'Tidak ada file yang diunggah.'})

def pegawai_export_import(request):
    """Display the export/import page for Pegawai data."""
    return render(request, 'pegawai/pegawai_export_import.html')

def _get_konversi_report_data(pegawai, ak_record_ids, include_integrasi, include_pendidikan=False):
    """Helper function to generate data for the Konversi report."""

    ak_records_for_report_qs = AK.objects.filter(pegawai=pegawai)
    if ak_record_ids:
        ak_records_for_report_qs = ak_records_for_report_qs.filter(id__in=ak_record_ids)

    ak_records_for_report_qs = ak_records_for_report_qs.order_by('tanggal_awal_penilaian')

    latest_ak = ak_records_for_report_qs.last()

    tahun = datetime.now().year
    if latest_ak and latest_ak.tanggal_akhir_penilaian:
        tahun = latest_ak.tanggal_akhir_penilaian.year
    elif latest_ak and latest_ak.tanggal_ditetapkan:
        tahun = latest_ak.tanggal_ditetapkan.year

    jenjang_raw = ""
    if latest_ak and latest_ak.jenjang:
        jenjang_raw = latest_ak.jenjang

    # Use the actual job title from the employee record instead of defaulting to "Analis"
    tmt_jabatan_str = ""
    if pegawai.tmt_jabatan:
        tmt_jabatan_str = pegawai.tmt_jabatan.strftime('%d-%m-%Y')
    jabatan_dan_tmt = f"{pegawai.jabatan} / {tmt_jabatan_str}" if tmt_jabatan_str else pegawai.jabatan

    periode_awal_str = ''
    periode_akhir_str = ''
    if ak_records_for_report_qs.exists():
        min_tgl_awal = ak_records_for_report_qs.aggregate(models.Min('tanggal_awal_penilaian'))['tanggal_awal_penilaian__min']
        max_tgl_akhir = ak_records_for_report_qs.aggregate(models.Max('tanggal_akhir_penilaian'))['tanggal_akhir_penilaian__max']
        if min_tgl_awal:
            periode_awal_str = min_tgl_awal.strftime('%d-%m-%Y')
        if max_tgl_akhir:
            periode_akhir_str = max_tgl_akhir.strftime('%d-%m-%Y')

    total_angka_kredit = 0.0
    ak_list_for_report = list(ak_records_for_report_qs)
    for ak_item in ak_list_for_report:
        total_angka_kredit += ak_item.jumlah_angka_kredit

    angka_integrasi_value = 0.0
    if include_integrasi:
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        if angka_integrasi_obj:
            angka_integrasi_value = angka_integrasi_obj.jumlah_angka_integrasi
            total_angka_kredit += angka_integrasi_value

    # Handle Ak Pendidikan
    ak_pendidikan_value = 0.0
    ak_pendidikan_list = []
    if include_pendidikan:
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)
        for ak_pend in ak_pendidikan_records:
            ak_pendidikan_value += ak_pend.jumlah_angka_kredit
            # Create a dictionary representation for display in the template
            ak_pend_dict = {
                'id': f'pendidikan_{ak_pend.id}',
                'jenis_kegiatan': ak_pend.jenis_kegiatan,
                'tanggal_pelaksanaan': ak_pend.tanggal_pelaksanaan,
                'jumlah_angka_kredit': ak_pend.jumlah_angka_kredit,
                'is_pendidikan_item': True,
                'nomor_sertifikat': ak_pend.nomor_sertifikat,
            }
            ak_pendidikan_list.append(ak_pend_dict)

        total_angka_kredit += ak_pendidikan_value

    report_data = {
        'pegawai': pegawai,
        'ak_list': ak_list_for_report,
        'tahun': tahun,
        'nama_instansi': latest_ak.instansi.nama_instansi if latest_ak else '',
        'periode_awal_str': periode_awal_str,
        'periode_akhir_str': periode_akhir_str,
        'jabatan_dan_tmt': jabatan_dan_tmt,
        'total_angka_kredit': total_angka_kredit,
        'include_angka_integrasi': include_integrasi,
        'angka_integrasi_value': angka_integrasi_value,
        'include_ak_pendidikan': include_pendidikan,
        'ak_pendidikan_value': ak_pendidikan_value,
        'ak_pendidikan_list': ak_pendidikan_list,
        'tempat_ditetapkan': latest_ak.tempat_ditetapkan if latest_ak else '',
        'tanggal_ditetapkan': latest_ak.tanggal_ditetapkan if latest_ak else datetime.now().date(),
        'nama_penilai': latest_ak.penilai.nama if latest_ak and latest_ak.penilai else '',
        'nip_penilai': latest_ak.penilai.nip if latest_ak and latest_ak.penilai else '',
        'pangkat_penilai': latest_ak.penilai.pangkat if latest_ak and latest_ak.penilai else '',
        'golongan_penilai': latest_ak.penilai.golongan if latest_ak and latest_ak.penilai else '',
    }
    return report_data, ak_list_for_report


def konversi_view(request):
    pegawai_options = Pegawai.objects.all()
    report_data = {}
    ak_list_for_report = []
    report_generated = False

    pegawai_id = request.POST.get('pegawai_id') or request.GET.get('pegawai_id')
    selected_period_ids = request.POST.getlist('selected_periods')
    include_angka_integrasi_str = request.POST.get('include_angka_integrasi', 'false')
    include_angka_integrasi = include_angka_integrasi_str.lower() == 'true'
    include_ak_pendidikan_str = request.POST.get('include_ak_pendidikan', 'false')
    include_ak_pendidikan = include_ak_pendidikan_str.lower() == 'true'

    all_ak_records_for_pegawai = []
    angka_integrasi_obj = None
    ak_pendidikan_records = []

    if pegawai_id:
        pegawai = get_object_or_404(Pegawai, id=pegawai_id)
        all_ak_records_for_pegawai = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)

        # If the form was submitted to generate a report
        if request.method == 'POST':
            # Default to all periods if none are selected, but only if the button was pushed
            use_all_periods = not selected_period_ids and 'pegawai_id' in request.POST

            final_period_ids = selected_period_ids
            if use_all_periods:
                final_period_ids = [str(ak.id) for ak in all_ak_records_for_pegawai]

            report_data, ak_list_for_report = _get_konversi_report_data(pegawai, final_period_ids, include_angka_integrasi, include_ak_pendidikan)
            report_generated = True

    context = {
        'pegawai_options': pegawai_options,
        'report_generated': report_generated,
        'report_data': report_data,
        'ak_list': ak_list_for_report,
        'selected_pegawai_id': int(pegawai_id) if pegawai_id else None,
        'all_ak_records': all_ak_records_for_pegawai,
        'ak_pendidikan_records': ak_pendidikan_records,
        'angka_integrasi_obj': angka_integrasi_obj,
        'selected_period_ids': [int(p) for p in selected_period_ids] if all(isinstance(p, str) and p.isdigit() for p in selected_period_ids) else selected_period_ids,
        'include_angka_integrasi': include_angka_integrasi,
        'include_ak_pendidikan': include_ak_pendidikan,
    }
    return render(request, 'pegawai/konversi.html', context)


def konversi_pdf_view(request):
    pegawai_id = request.GET.get('pegawai_id')
    if not pegawai_id:
        return HttpResponse("Pegawai ID is required.", status=400)

    selected_period_ids = request.GET.getlist('selected_periods')
    include_angka_integrasi_str = request.GET.get('include_angka_integrasi', 'false')
    include_angka_integrasi = include_angka_integrasi_str.lower() == 'true'
    include_ak_pendidikan_str = request.GET.get('include_ak_pendidikan', 'false')
    include_ak_pendidikan = include_ak_pendidikan_str.lower() == 'true'

    pegawai = get_object_or_404(Pegawai, id=pegawai_id)

    # If no periods are passed, get all of them for the report
    if not selected_period_ids:
        selected_period_ids = list(AK.objects.filter(pegawai=pegawai).values_list('id', flat=True))

    report_data, ak_list_for_report = _get_konversi_report_data(pegawai, selected_period_ids, include_angka_integrasi, include_ak_pendidikan)

    context = {
        'report_data': report_data,
        'ak_list': ak_list_for_report,
        'base_dir': settings.BASE_DIR,
    }
    pdf = render_to_pdf('pegawai/konversi_report_template.html', context)
    if pdf:
        return pdf
    return HttpResponse("Error generating PDF", status=500)


def akumulasi_view(request):
    pegawai_options = Pegawai.objects.all()
    report_data = {}
    ak_list_for_report = []
    report_generated = False

    pegawai_id = request.POST.get('pegawai_id') or request.GET.get('pegawai_id')
    selected_periods = request.POST.getlist('selected_periods') # Get selected period IDs
    include_ak_pendidikan_str = request.POST.get('include_ak_pendidikan', 'false')
    include_ak_pendidikan = include_ak_pendidikan_str.lower() == 'true'

    # Get all AK records for the selected pegawai (for dropdown options)
    all_ak_records_for_pegawai = []
    if pegawai_id:
        pegawai_obj = get_object_or_404(Pegawai, id=pegawai_id)
        all_ak_records_for_pegawai = list(AK.objects.filter(pegawai=pegawai_obj).order_by('tanggal_awal_penilaian'))

        # Add AK Integrasi as a selectable option if it exists
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai_obj).first()
        if angka_integrasi_obj:
            integrasi_option = {
                'id': 'integrasi_ak', # Unique string identifier for this option
                'penilaian': 'AK Integrasi',
                'tanggal_awal_penilaian': None, # Not applicable for display in dropdown
                'tanggal_akhir_penilaian': None, # Not applicable for display in dropdown
                'is_integrasi_option': True, # Custom flag to identify this item
            }
            # Insert at the beginning of the list to show first in dropdown
            all_ak_records_for_pegawai.insert(0, integrasi_option)

        # Add Ak Pendidikan as a selectable option if it exists
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai_obj)
        if ak_pendidikan_records.exists():
            pendidikan_option = {
                'id': 'pendidikan_ak', # Unique string identifier for this option
                'penilaian': 'AK Pendidikan',
                'tanggal_awal_penilaian': None, # Not applicable for display in dropdown
                'tanggal_akhir_penilaian': None, # Not applicable for display in dropdown
                'is_pendidikan_option': True, # Custom flag to identify this item
            }
            # Insert after integrasi option to show in dropdown
            all_ak_records_for_pegawai.insert(1, pendidikan_option)


    ak_records_filtered = AK.objects.none() # Initialize as an empty QuerySet

    if pegawai_id:
        pegawai = get_object_or_404(Pegawai, id=pegawai_id)
        jabatan_fungsional = "Analis" # Initialize with a default value

        # Fetch the true latest AK record for the selected pegawai, regardless of filters
        latest_ak_unfiltered = AK.objects.filter(pegawai=pegawai).order_by('tanggal_akhir_penilaian').last()

        # Separate selected_periods into actual AK IDs and flags for Integrasi and Pendidikan
        selected_ak_ids = []
        include_integrasi_filter = False
        include_pendidikan_filter = False
        if selected_periods: # Only process if something was selected
            for p_id in selected_periods:
                if p_id == 'integrasi_ak':
                    include_integrasi_filter = True
                elif p_id == 'pendidikan_ak':
                    include_pendidikan_filter = True
                else:
                    try:
                        selected_ak_ids.append(int(p_id))
                    except ValueError:
                        pass # Ignore invalid IDs

        # Build the initial queryset for AK records
        ak_records_queryset = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')

        # Filter ak_records based on selected_ak_ids, if any were selected
        # If selected_periods is not empty, and 'integrasi_ak' was selected, but no actual AK IDs,
        # then we should only show integrasi. If no selections at all, show all AKs.
        if selected_periods and selected_ak_ids: # If specific AKs were selected
            ak_records_filtered = ak_records_queryset.filter(id__in=selected_ak_ids)
        elif selected_periods and not selected_ak_ids and include_integrasi_filter: # Only integrasi was selected
            ak_records_filtered = AK.objects.none() # Empty QuerySet, only integrasi will be added manually
        else: # No filters selected, or only invalid filters, show all AKs
            ak_records_filtered = ak_records_queryset.all()


        latest_ak = None
        if isinstance(ak_records_filtered, models.QuerySet):
            latest_ak = ak_records_filtered.last()
        elif isinstance(ak_records_filtered, list) and ak_records_filtered:
            # Find the last actual AK object, not the integrasi_ak_item_display dict
            for item in reversed(ak_records_filtered):
                if not isinstance(item, dict) or not item.get('is_integrasi_item', False):
                    latest_ak = item
                    break

        tahun = datetime.now().year
        jenjang_raw = ""

        if latest_ak_unfiltered and latest_ak_unfiltered.tanggal_akhir_penilaian:
            tahun = latest_ak_unfiltered.tanggal_akhir_penilaian.year
            if latest_ak_unfiltered.jenjang:
                jenjang_raw = latest_ak_unfiltered.jenjang
        elif latest_ak_unfiltered and latest_ak_unfiltered.tanggal_ditetapkan:
            tahun = latest_ak_unfiltered.tanggal_ditetapkan.year
            if latest_ak_unfiltered.jenjang:
                jenjang_raw = latest_ak_unfiltered.jenjang

        # Use the actual job title from the employee record instead of defaulting to "Analis"
        tmt_jabatan_str = ""
        if pegawai.tmt_jabatan:
            tmt_jabatan_str = pegawai.tmt_jabatan.strftime('%d-%m-%Y')
        jabatan_dan_tmt = f"{pegawai.jabatan} / {tmt_jabatan_str}" if tmt_jabatan_str else pegawai.jabatan

        periode_awal_str = ''
        periode_akhir_str = ''
        # These need to be based on the actual AK records in ak_list_for_report, not ak_records_queryset

        # Initialize ak_list_for_report from filtered ak_records
        ak_list_for_report = list(ak_records_filtered)

        if ak_list_for_report: # Check if ak_list_for_report is not empty after filtering and integrasi
            min_tgl_awal_filtered = None
            max_tgl_akhir_filtered = None
            # Find min and max dates from ak_list_for_report (excluding integrasi_ak_item if it has no dates)
            for item in ak_list_for_report:
                # Check if it's an Integrasi item (which is a dict)
                is_integrasi = isinstance(item, dict) and item.get('is_integrasi_item', False)

                if not is_integrasi: # Only consider actual AK records
                    # Access attributes safely for model instances
                    tanggal_awal = getattr(item, 'tanggal_awal_penilaian', None)
                    tanggal_akhir = getattr(item, 'tanggal_akhir_penilaian', None)

                    if not min_tgl_awal_filtered or (tanggal_awal and tanggal_awal < min_tgl_awal_filtered):
                        min_tgl_awal_filtered = tanggal_awal
                    if not max_tgl_akhir_filtered or (tanggal_akhir and tanggal_akhir > max_tgl_akhir_filtered):
                        max_tgl_akhir_filtered = tanggal_akhir

            if min_tgl_awal_filtered:
                periode_awal_str = min_tgl_awal_filtered.strftime('%d-%m-%Y')
            if max_tgl_akhir_filtered:
                periode_akhir_str = max_tgl_akhir_filtered.strftime('%d-%m-%Y')
        total_angka_kredit = 0.0

        for ak_item in ak_list_for_report: # Iterate over the actual records for total
            total_angka_kredit += ak_item.jumlah_angka_kredit

            if ak_item.tanggal_awal_penilaian and ak_item.tanggal_akhir_penilaian:
                rdelta = relativedelta(ak_item.tanggal_akhir_penilaian, ak_item.tanggal_awal_penilaian)
                months = rdelta.years * 12 + rdelta.months
                if rdelta.days > 0:
                    months += 1
                if months == 0: months = 1
                ak_item.periode_bulan = months
            else:
                ak_item.periode_bulan = 0

        # Handle AK Integrasi separately for display in ak_list_for_report
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        if angka_integrasi_obj:
            angka_integrasi_value = angka_integrasi_obj.jumlah_angka_integrasi

            # If 'integrasi_ak' was selected OR no filters were selected (show all)
            if include_integrasi_filter or not selected_periods:
                total_angka_kredit += angka_integrasi_value # Add to total only if included in report

                # Create a dummy AK item for Integrasi
                integrasi_ak_item_display = {
                    'id': 'integrasi_ak',
                    'tanggal_awal_penilaian': None, # Not applicable
                    'periode_bulan': None, # Not applicable
                    'penilaian': 'AK Integrasi',
                    'prosentase': None, # Not applicable
                    'koefisien': None, # Not applicable
                    'jumlah_angka_kredit': angka_integrasi_value,
                    'is_integrasi_item': True, # Custom flag for template
                }
                # Prepend to the list
                ak_list_for_report.insert(0, integrasi_ak_item_display)

        # Handle Ak Pendidikan separately for display in ak_list_for_report
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)
        if ak_pendidikan_records.exists():
            ak_pendidikan_total = sum([ak_pend.jumlah_angka_kredit for ak_pend in ak_pendidikan_records])

            # If 'pendidikan_ak' was selected OR no filters were selected (show all)
            if include_pendidikan_filter or not selected_periods:
                total_angka_kredit += ak_pendidikan_total # Add to total only if included in report

                # Create a dummy AK item for Pendidikan
                pendidikan_ak_item_display = {
                    'id': 'pendidikan_ak',
                    'tanggal_awal_penilaian': None, # Not applicable
                    'periode_bulan': None, # Not applicable
                    'penilaian': 'AK Pendidikan',
                    'prosentase': None, # Not applicable
                    'koefisien': None, # Not applicable
                    'jumlah_angka_kredit': ak_pendidikan_total,
                    'is_pendidikan_item': True, # Custom flag for template
                }
                # Prepend to the list after integrasi if present
                insert_index = 1 if include_integrasi_filter or (not selected_periods and angka_integrasi_obj) else 0
                ak_list_for_report.insert(insert_index, pendidikan_ak_item_display)

        report_data = {
            'pegawai': pegawai,
            'ak_list': ak_list_for_report,
            'tahun': tahun,
            'nama_instansi': latest_ak.instansi.nama_instansi if latest_ak else '',
            'periode_awal_str': periode_awal_str,
            'periode_akhir_str': periode_akhir_str,
            'jabatan_dan_tmt': jabatan_dan_tmt,
            'total_angka_kredit': total_angka_kredit,
            'tempat_ditetapkan': latest_ak.tempat_ditetapkan if latest_ak else '',
            'tanggal_ditetapkan': latest_ak.tanggal_ditetapkan if latest_ak else datetime.now().date(),
            'nama_penilai': latest_ak.penilai.nama if latest_ak and latest_ak.penilai else '',
            'nip_penilai': latest_ak.penilai.nip if latest_ak and latest_ak.penilai else '',
            'pangkat_penilai': latest_ak.penilai.pangkat if latest_ak and latest_ak.penilai else '',
            'golongan_penilai': latest_ak.penilai.golongan if latest_ak and latest_ak.penilai else '',
        }
        report_generated = True

    context = {
        'pegawai_options': pegawai_options,
        'all_ak_records': all_ak_records_for_pegawai, # Pass all AK records for the dropdown
        'selected_periods': selected_periods, # Pass selected period IDs for the dropdown to retain state
        'report_generated': report_generated,
        'report_data': report_data,
        'ak_list': ak_list_for_report,
        'selected_pegawai_id': int(pegawai_id) if pegawai_id else None,
        'include_ak_pendidikan': include_ak_pendidikan,  # Pass the flag to template
    }
    return render(request, 'pegawai/akumulasi.html', context)


def akumulasi_pdf_view(request):
    pegawai_id = request.GET.get('pegawai_id')
    if not pegawai_id:
        return HttpResponse("Pegawai ID is required.", status=400)

    selected_periods = request.GET.getlist('selected_periods') # Get selected period IDs
    include_ak_pendidikan_str = request.GET.get('include_ak_pendidikan', 'false')
    include_ak_pendidikan = include_ak_pendidikan_str.lower() == 'true'

    pegawai = get_object_or_404(Pegawai, id=pegawai_id)

    # Separate selected_periods into actual AK IDs and flags for Integrasi and Pendidikan
    selected_ak_ids = []
    include_integrasi_filter = False
    include_pendidikan_filter = False
    if selected_periods: # Only process if something was selected
        for p_id in selected_periods:
            if p_id == 'integrasi_ak':
                include_integrasi_filter = True
            elif p_id == 'pendidikan_ak':
                include_pendidikan_filter = True
            else:
                try:
                    selected_ak_ids.append(int(p_id))
                except ValueError:
                    pass # Ignore invalid IDs

    # If no periods are passed, get all of them for the report
    if not selected_periods:
        selected_ak_ids = list(AK.objects.filter(pegawai=pegawai).values_list('id', flat=True))
        if AngkaIntegrasi.objects.filter(pegawai=pegawai).exists():
            include_integrasi_filter = True
        if AkPendidikan.objects.filter(pegawai=pegawai).exists():
            include_pendidikan_filter = True


    report_data = _get_akumulasi_report_data(pegawai, selected_ak_ids, include_integrasi_filter, include_pendidikan_filter)

    context = {
        'report_data': report_data,
        'ak_list': report_data.get('ak_list', []),
        'base_dir': settings.BASE_DIR,
    }
    pdf = render_to_pdf('pegawai/akumulasi_report_template.html', context)
    if pdf:
        return pdf
    return HttpResponse("Error generating PDF", status=500)

def penetapan_view(request):
    pegawai_options = Pegawai.objects.all()
    report_data = {}
    ak_list_for_report = []
    report_generated = False
    pegawai_id = request.POST.get('pegawai_id') or request.GET.get('pegawai_id')
    selected_periods = request.POST.getlist('selected_periods')  # Get selected period IDs
    include_ak_pendidikan_str = request.POST.get('include_ak_pendidikan', 'false')
    include_ak_pendidikan = include_ak_pendidikan_str.lower() == 'true'

    # Get all AK records for the selected pegawai (for dropdown options)
    all_ak_records_for_pegawai = []
    if pegawai_id:
        pegawai_obj = get_object_or_404(Pegawai, id=pegawai_id)
        all_ak_records_for_pegawai = list(AK.objects.filter(pegawai=pegawai_obj).order_by('tanggal_awal_penilaian'))
        # Add AK Integrasi as a selectable option if it exists
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai_obj).first()
        if angka_integrasi_obj:
            integrasi_option = {
                'id': 'integrasi_ak',
                'penilaian': 'AK Integrasi',
                'tanggal_awal_penilaian': None,
                'tanggal_akhir_penilaian': None,
                'is_integrasi_option': True,
            }
            all_ak_records_for_pegawai.insert(0, integrasi_option)

        # Add Ak Pendidikan as a selectable option if it exists
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai_obj)
        if ak_pendidikan_records.exists():
            pendidikan_option = {
                'id': 'pendidikan_ak',
                'penilaian': 'AK Pendidikan',
                'tanggal_awal_penilaian': None,
                'tanggal_akhir_penilaian': None,
                'is_pendidikan_option': True,
            }
            all_ak_records_for_pegawai.insert(1, pendidikan_option)

    ak_records_filtered = AK.objects.none()  # Initialize as an empty QuerySet

    if pegawai_id:
        pegawai = get_object_or_404(Pegawai, id=pegawai_id)
        # Fetch the true latest AK record for the selected pegawai, regardless of filters
        latest_ak_unfiltered = AK.objects.filter(pegawai=pegawai).order_by('tanggal_akhir_penilaian').last()

        # Separate selected_periods into actual AK IDs and flags for Integrasi and Pendidikan
        selected_ak_ids = []
        include_integrasi_filter = False
        include_pendidikan_filter = False
        if selected_periods:  # Only process if something was selected
            for p_id in selected_periods:
                if p_id == 'integrasi_ak':
                    include_integrasi_filter = True
                elif p_id == 'pendidikan_ak':
                    include_pendidikan_filter = True
                else:
                    try:
                        selected_ak_ids.append(int(p_id))
                    except ValueError:
                        pass  # Ignore invalid IDs

        # Build the initial queryset for AK records
        ak_records_queryset = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')

        # Filter ak_records based on selected_ak_ids
        if selected_periods and selected_ak_ids:
            ak_records_filtered = ak_records_queryset.filter(id__in=selected_ak_ids)
        elif selected_periods and not selected_ak_ids and include_integrasi_filter:
            ak_records_filtered = AK.objects.none()
        else:
            ak_records_filtered = ak_records_queryset.all()

        latest_ak = None
        if isinstance(ak_records_filtered, models.QuerySet):
            latest_ak = ak_records_filtered.last()
        elif isinstance(ak_records_filtered, list) and ak_records_filtered:
            for item in reversed(ak_records_filtered):
                if not isinstance(item, dict) or not item.get('is_integrasi_item', False):
                    latest_ak = item
                    break

        tahun = datetime.now().year
        if latest_ak_unfiltered and latest_ak_unfiltered.tanggal_akhir_penilaian:
            tahun = latest_ak_unfiltered.tanggal_akhir_penilaian.year
        elif latest_ak_unfiltered and latest_ak_unfiltered.tanggal_ditetapkan:
            tahun = latest_ak_unfiltered.tanggal_ditetapkan.year

        # === MODIFIKASI UTAMA: PENYESUAIAN BERDASARKAN GOLONGAN ===
        raw_golongan = str(pegawai.golongan).strip()
        # Normalisasi alternatif format golongan
        alt_map = {
            "IIIA": "III/a",
            "IIIB": "III/b",
            "IIIC": "III/c",
            "IIID": "III/d",
            "3A": "III/a",
            "3B": "III/b",
            "3C": "III/c",
            "3D": "III/d",
            "3a": "III/a",
            "3b": "III/b",
            "3c": "III/c",
            "3d": "III/d",
        }
        golongan = alt_map.get(raw_golongan.upper(), raw_golongan)

        total_lama = GOLONGAN_TO_LAMA.get(golongan, 0.0)

        # Hitung total_baru dari AK terpilih
        total_baru = 0.0
        ak_list_for_report = list(ak_records_filtered)
        for ak_item in ak_list_for_report:
            total_baru += ak_item.jumlah_angka_kredit

        # Tambahkan AK Integrasi jika relevan
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        if angka_integrasi_obj:
            angka_integrasi_value = angka_integrasi_obj.jumlah_angka_integrasi
            if include_integrasi_filter or not selected_periods:
                total_baru += angka_integrasi_value
                integrasi_ak_item_display = {
                    'id': 'integrasi_ak',
                    'tanggal_awal_penilaian': None,
                    'periode_bulan': None,
                    'penilaian': 'AK Integrasi',
                    'prosentase': None,
                    'koefisien': None,
                    'jumlah_angka_kredit': angka_integrasi_value,
                    'is_integrasi_item': True,
                }
                ak_list_for_report.insert(0, integrasi_ak_item_display)

        # Tambahkan AK Pendidikan jika relevan
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)
        ak_pendidikan_total = 0
        if ak_pendidikan_records.exists():
            ak_pendidikan_total = sum([ak_pend.jumlah_angka_kredit for ak_pend in ak_pendidikan_records])
            if include_pendidikan_filter or not selected_periods:
                # NOTE: For penetapan report, pendidikan is shown in a separate row, not added to total_baru
                pendidikan_ak_item_display = {
                    'id': 'pendidikan_ak',
                    'tanggal_awal_penilaian': None,
                    'periode_bulan': None,
                    'penilaian': 'AK Pendidikan',
                    'prosentase': None,
                    'koefisien': None,
                    'jumlah_angka_kredit': ak_pendidikan_total,
                    'is_pendidikan_item': True,
                }
                # Insert after integrasi if present, otherwise at the beginning
                insert_index = 1 if include_integrasi_filter or (not selected_periods and angka_integrasi_obj) else 0
                ak_list_for_report.insert(insert_index, pendidikan_ak_item_display)

        # === TERAPKAN PENGURANGAN SESUAI GOLONGAN ===
        PENGURANGAN_GOLONGAN = {
            "III/a": 0,
            "III/b": 50,
            "III/c": 0,
            "III/d": 100,
        }
        pengurangan = PENGURANGAN_GOLONGAN.get(golongan, 0)
        total_baru = max(0.0, total_baru - pengurangan)  # Hindari nilai negatif

        # For penetapan report, total_jumlah includes ak_pendidikan_total if included
        total_jumlah = total_lama + total_baru + ak_pendidikan_total

        # Hitung info kenaikan pangkat
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

        PANGKAT_OPTIONS_REVERSE = {v: k for k, v in PANGKAT_OPTIONS.items()}
        if next_golongan in GOLONGAN_HIERARKI:
            nama_pangkat_tujuan = PANGKAT_OPTIONS_REVERSE.get(next_golongan, next_golongan)
            teks_tujuan = f"{nama_pangkat_tujuan} {next_golongan}"
        else:
            teks_tujuan = next_golongan

        hasil_pangkat = total_jumlah - pangkat_minimal
        hasil_jenjang = total_jumlah - jenjang_minimal

        # Jabatan dan TMT
        jenjang_raw = ""
        if latest_ak_unfiltered and latest_ak_unfiltered.jenjang:
            jenjang_raw = latest_ak_unfiltered.jenjang
        # Use the actual job title from the employee record instead of defaulting to "Analis"
        tmt_jabatan_str = ""
        if pegawai.tmt_jabatan:
            tmt_jabatan_str = pegawai.tmt_jabatan.strftime('%d-%m-%Y')
        jabatan_dan_tmt = f"{pegawai.jabatan} / {tmt_jabatan_str}" if tmt_jabatan_str else pegawai.jabatan

        # Periode awal & akhir
        periode_awal_str = ''
        periode_akhir_str = ''
        if ak_list_for_report:
            min_tgl_awal_filtered = None
            max_tgl_akhir_filtered = None
            for item in ak_list_for_report:
                is_integrasi = isinstance(item, dict) and item.get('is_integrasi_item', False)
                is_pendidikan = isinstance(item, dict) and item.get('is_pendidikan_item', False)
                if not is_integrasi and not is_pendidikan:
                    tanggal_awal = getattr(item, 'tanggal_awal_penilaian', None)
                    tanggal_akhir = getattr(item, 'tanggal_akhir_penilaian', None)
                    if not min_tgl_awal_filtered or (tanggal_awal and tanggal_awal < min_tgl_awal_filtered):
                        min_tgl_awal_filtered = tanggal_awal
                    if not max_tgl_akhir_filtered or (tanggal_akhir and tanggal_akhir > max_tgl_akhir_filtered):
                        max_tgl_akhir_filtered = tanggal_akhir
            if min_tgl_awal_filtered:
                periode_awal_str = min_tgl_awal_filtered.strftime('%d-%m-%Y')
            if max_tgl_akhir_filtered:
                periode_akhir_str = max_tgl_akhir_filtered.strftime('%d-%m-%Y')

        report_data = {
            'pegawai': pegawai,
            'ak_list': ak_list_for_report,
            'tahun': tahun,
            'nama_instansi': latest_ak_unfiltered.instansi.nama_instansi if latest_ak_unfiltered and latest_ak_unfiltered.instansi else '',
            'periode_awal_str': periode_awal_str,
            'periode_akhir_str': periode_akhir_str,
            'jabatan_dan_tmt': jabatan_dan_tmt,
            'total_lama': total_lama,
            'total_baru': total_baru,          # <-- SUDAH DIKURANGI SESUAI GOLONGAN
            'total_jumlah': total_jumlah,
            'ak_pendidikan_value': ak_pendidikan_total,
            'total_performance_only': total_lama + total_baru,
            'total_baru_with_pendidikan': total_baru + ak_pendidikan_total,
            'pangkat_minimal': pangkat_minimal,
            'jenjang_minimal': jenjang_minimal,
            'hasil_pangkat': hasil_pangkat,
            'hasil_jenjang': hasil_jenjang,
            'teks_tujuan': teks_tujuan,
            'tempat_ditetapkan': latest_ak_unfiltered.tempat_ditetapkan if latest_ak_unfiltered else '',
            'tanggal_ditetapkan': latest_ak_unfiltered.tanggal_ditetapkan if latest_ak_unfiltered else datetime.now().date(),
            'nama_penilai': latest_ak_unfiltered.penilai.nama if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
            'nip_penilai': latest_ak_unfiltered.penilai.nip if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
            'pangkat_penilai': latest_ak_unfiltered.penilai.pangkat if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
            'golongan_penilai': latest_ak_unfiltered.penilai.golongan if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
        }
        report_generated = True

    context = {
        'pegawai_options': pegawai_options,
        'all_ak_records': all_ak_records_for_pegawai,
        'selected_periods': selected_periods,
        'report_generated': report_generated,
        'report_data': report_data,
        'ak_list': ak_list_for_report,
        'selected_pegawai_id': int(pegawai_id) if pegawai_id else None,
        'include_ak_pendidikan': include_ak_pendidikan,  # Pass the flag to template
    }
    return render(request, 'pegawai/penetapan.html', context)

def penetapan_pdf_view(request):
    pegawai_id = request.GET.get('pegawai_id')
    if not pegawai_id:
        return HttpResponse("Pegawai ID is required.", status=400)

    selected_periods = request.GET.getlist('selected_periods')
    include_ak_pendidikan_str = request.GET.get('include_ak_pendidikan', 'false')
    include_ak_pendidikan = include_ak_pendidikan_str.lower() == 'true'
    pegawai = get_object_or_404(Pegawai, id=pegawai_id)

    selected_ak_ids = []
    include_integrasi_filter = False
    include_pendidikan_filter = False
    if selected_periods:
        for p_id in selected_periods:
            if p_id == 'integrasi_ak':
                include_integrasi_filter = True
            elif p_id == 'pendidikan_ak':
                include_pendidikan_filter = True
            else:
                try:
                    selected_ak_ids.append(int(p_id))
                except ValueError:
                    pass

    if not selected_periods:
        selected_ak_ids = list(AK.objects.filter(pegawai=pegawai).values_list('id', flat=True))
        if AngkaIntegrasi.objects.filter(pegawai=pegawai).exists():
            include_integrasi_filter = True
        if AkPendidikan.objects.filter(pegawai=pegawai).exists():
            include_pendidikan_filter = True

    report_data = _get_penetapan_report_data(pegawai, selected_ak_ids, include_integrasi_filter, include_pendidikan_filter)

    context = {
        'report_data': report_data,
        'ak_list': report_data.get('ak_list', []),
        'base_dir': settings.BASE_DIR,
    }
    pdf = render_to_pdf('pegawai/penetapan_report_template.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="penetapan_{pegawai.nip}.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)

def angka_integrasi_list(request):
    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # Start with all AngkaIntegrasi objects, ordered by employee name in ascending order
    angka_integrasi_list = AngkaIntegrasi.objects.select_related('pegawai').order_by('pegawai__nama')

    # If there's a search query, filter by employee name
    if search_query:
        angka_integrasi_list = angka_integrasi_list.filter(pegawai__nama__icontains=search_query)

    # Apply pagination
    paginator = Paginator(angka_integrasi_list, 5)  # Show 5 records per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pegawai/angka_integrasi_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

def instruction_manual_pdf(request):
    """Generate and serve the instruction manual PDF."""
    context = {
        'title': 'Petunjuk Penggunaan Aplikasi AppAk',
        'sections': [
            {
                'title': '1. Pendahuluan',
                'content': [
                    'Aplikasi AppAk adalah sistem manajemen Angka Kredit untuk pegawai.',
                    'Aplikasi ini membantu dalam pengelolaan data pegawai, penilai, instansi, serta perhitungan Angka Kredit.'
                ]
            },
            {
                'title': '2. Manajemen Data Pegawai',
                'content': [
                    'Menu ini digunakan untuk mengelola data pegawai.',
                    'Anda dapat menambah, mengedit, atau menghapus data pegawai.',
                    'Fitur pencarian dan paginasi tersedia untuk kemudahan penggunaan.'
                ]
            },
            {
                'title': '3. Manajemen Data Instansi',
                'content': [
                    'Menu ini digunakan untuk mengelola data instansi.',
                    'Instansi merupakan tempat dimana pegawai bekerja.'
                ]
            },
            {
                'title': '4. Manajemen Data Penilai',
                'content': [
                    'Menu ini digunakan untuk mengelola data penilai.',
                    'Penilai adalah orang yang bertugas menilai kinerja pegawai.'
                ]
            },
            {
                'title': '5. Manajemen Angka Kredit',
                'content': [
                    'Menu ini digunakan untuk mengelola data Angka Kredit.',
                    'Anda dapat menambahkan data penilaian kinerja dan sistem akan menghitung Angka Kredit secara otomatis.'
                ]
            },
            {
                'title': '6. Angka Integrasi',
                'content': [
                    'Menu ini digunakan untuk mengelola data Angka Integrasi.',
                    'Angka Integrasi merupakan Angka Kredit tambahan yang diperoleh dari kegiatan lain.'
                ]
            },
            {
                'title': '7. Cetak Laporan',
                'content': [
                    'Menu ini digunakan untuk mencetak berbagai jenis laporan Angka Kredit.',
                    'Terdapat tiga jenis laporan: Konversi, Akumulasi, dan Penetapan.'
                ]
            },
            {
                'title': '8. Export/Import Data',
                'content': [
                    'Menu ini digunakan untuk mengekspor dan mengimpor data pegawai.',
                    'Format file yang digunakan adalah CSV.',
                    'Pastikan untuk menggunakan template yang telah disediakan untuk menghindari kesalahan format.'
                ]
            },
            {
                'title': '9. Mode Gelap/Cerah',
                'content': [
                    'Aplikasi mendukung mode gelap dan cerah.',
                    'Gunakan tombol toggle di pojok kanan atas untuk mengganti mode.'
                ]
            },
            {
                'title': '10. Panduan Import Data',
                'content': [
                    'Untuk mengimpor data pegawai, pastikan file CSV mengikuti format template.',
                    'Khusus untuk NIP, hindari konversi otomatis Excel ke format ilmiah (misalnya 1.23E+17).',
                    'Tambahkan petik satu (") sebelum NIP saat mengisi data di Excel, atau gunakan format teks.'
                ]
            }
        ]
    }

    pdf = render_to_pdf('pegawai/instruction_manual_template.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="petunjuk_penggunaan_appak.pdf"'
        return response
    return HttpResponse("Error generating PDF", status=500)

class AngkaIntegrasiCreateView(CreateView):
    model = AngkaIntegrasi
    form_class = AngkaIntegrasiForm
    template_name = 'pegawai/angka_integrasi_form.html'
    success_url = reverse_lazy('angka_integrasi_list')

class AngkaIntegrasiUpdateView(UpdateView):
    model = AngkaIntegrasi
    form_class = AngkaIntegrasiForm
    template_name = 'pegawai/angka_integrasi_form.html'
    success_url = reverse_lazy('angka_integrasi_list')

class AngkaIntegrasiDeleteView(DeleteView):
    model = AngkaIntegrasi
    template_name = 'pegawai/angka_integrasi_confirm_delete.html'
    success_url = reverse_lazy('angka_integrasi_list')

def instansi_list(request):
    instansi = Instansi.objects.all()
    return render(request, 'pegawai/instansi_list.html', {'instansi': instansi})

class InstansiCreateView(CreateView):
    model = Instansi
    form_class = InstansiForm
    template_name = 'pegawai/instansi_form.html'
    success_url = reverse_lazy('instansi_list')

class InstansiUpdateView(UpdateView):
    model = Instansi
    form_class = InstansiForm
    template_name = 'pegawai/instansi_form.html'
    success_url = reverse_lazy('instansi_list')

class InstansiDeleteView(DeleteView):
    model = Instansi
    template_name = 'pegawai/instansi_confirm_delete.html'
    success_url = reverse_lazy('instansi_list')

def penilai_list(request):
    penilai = Penilai.objects.all()
    return render(request, 'pegawai/penilai_list.html', {'penilai': penilai})

class PenilaiCreateView(CreateView):
    model = Penilai
    form_class = PenilaiForm
    template_name = 'pegawai/penilai_form.html'
    success_url = reverse_lazy('penilai_list')

class PenilaiUpdateView(UpdateView):
    model = Penilai
    form_class = PenilaiForm
    template_name = 'pegawai/penilai_form.html'
    success_url = reverse_lazy('penilai_list')

class PenilaiDeleteView(DeleteView):
    model = Penilai
    template_name = 'pegawai/penilai_confirm_delete.html'
    success_url = reverse_lazy('penilai_list')

from django.core.paginator import Paginator

def ak_list(request):
    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # Start with all AK objects, ordered by employee name in ascending order
    ak_list = AK.objects.select_related('pegawai', 'instansi', 'penilai').order_by('pegawai__nama')

    # If there's a search query, filter by employee name
    if search_query:
        ak_list = ak_list.filter(pegawai__nama__icontains=search_query)

    # Apply pagination
    paginator = Paginator(ak_list, 5)  # Show 5 records per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pegawai/ak_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

class AKCreateView(CreateView):
    model = AK
    form_class = AKForm
    template_name = 'pegawai/ak_form.html'
    success_url = reverse_lazy('ak_list')

    def form_valid(self, form):
        # Calculate fields before saving
        form.instance = _calculate_ak_fields(form.instance)
        return super().form_valid(form)

class AKUpdateView(UpdateView):
    model = AK
    form_class = AKForm
    template_name = 'pegawai/ak_form.html'
    success_url = reverse_lazy('ak_list')

    def form_valid(self, form):
        # Calculate fields before saving
        form.instance = _calculate_ak_fields(form.instance)
        return super().form_valid(form)

class AKDeleteView(DeleteView):
    model = AK
    template_name = 'pegawai/ak_confirm_delete.html'
    success_url = reverse_lazy('ak_list')


def ak_pendidikan_list(request):
    # Get the search query from the GET parameters
    search_query = request.GET.get('search', '')

    # Start with all AkPendidikan objects, ordered by employee name in ascending order
    ak_pendidikan_list = AkPendidikan.objects.select_related('pegawai', 'instansi', 'penilai').order_by('pegawai__nama')

    # If there's a search query, filter by employee name
    if search_query:
        ak_pendidikan_list = ak_pendidikan_list.filter(pegawai__nama__icontains=search_query)

    # Apply pagination
    paginator = Paginator(ak_pendidikan_list, 5)  # Show 5 records per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pegawai/ak_pendidikan_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })


class AkPendidikanCreateView(CreateView):
    model = AkPendidikan
    form_class = AkPendidikanForm
    template_name = 'pegawai/ak_pendidikan_form.html'
    success_url = reverse_lazy('ak_pendidikan_list')


class AkPendidikanUpdateView(UpdateView):
    model = AkPendidikan
    form_class = AkPendidikanForm
    template_name = 'pegawai/ak_pendidikan_form.html'
    success_url = reverse_lazy('ak_pendidikan_list')


class AkPendidikanDeleteView(DeleteView):
    model = AkPendidikan
    template_name = 'pegawai/ak_pendidikan_confirm_delete.html'
    success_url = reverse_lazy('ak_pendidikan_list')


def _get_akumulasi_report_data(pegawai, selected_ak_ids, include_integrasi_filter, include_pendidikan_filter=False):
    # This is a simplified version of the logic in akumulasi_view
    ak_records_queryset = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')

    if selected_ak_ids:
        ak_records_filtered = ak_records_queryset.filter(id__in=selected_ak_ids)
    else:
        ak_records_filtered = ak_records_queryset.all()

    latest_ak_unfiltered = AK.objects.filter(pegawai=pegawai).order_by('tanggal_akhir_penilaian').last()

    latest_ak = ak_records_filtered.last() if ak_records_filtered.exists() else None

    tahun = datetime.now().year
    if latest_ak_unfiltered and latest_ak_unfiltered.tanggal_akhir_penilaian:
        tahun = latest_ak_unfiltered.tanggal_akhir_penilaian.year
    elif latest_ak_unfiltered and latest_ak_unfiltered.tanggal_ditetapkan:
        tahun = latest_ak_unfiltered.tanggal_ditetapkan.year

    jenjang_raw = ""
    if latest_ak_unfiltered and latest_ak_unfiltered.jenjang:
        jenjang_raw = latest_ak_unfiltered.jenjang
    # Use the actual job title from the employee record instead of defaulting to "Analis"
    tmt_jabatan_str = ""
    if pegawai.tmt_jabatan:
        tmt_jabatan_str = pegawai.tmt_jabatan.strftime('%d-%m-%Y')
    jabatan_dan_tmt = f"{pegawai.jabatan} / {tmt_jabatan_str}" if tmt_jabatan_str else pegawai.jabatan

    periode_awal_str, periode_akhir_str = '', ''
    ak_list_for_report = list(ak_records_filtered)

    if ak_list_for_report:
        min_tgl_awal = min((ak.tanggal_awal_penilaian for ak in ak_list_for_report if hasattr(ak, 'tanggal_awal_penilaian') and ak.tanggal_awal_penilaian), default=None)
        max_tgl_akhir = max((ak.tanggal_akhir_penilaian for ak in ak_list_for_report if hasattr(ak, 'tanggal_akhir_penilaian') and ak.tanggal_akhir_penilaian), default=None)
        if min_tgl_awal:
            periode_awal_str = min_tgl_awal.strftime('%d-%m-%Y')
        if max_tgl_akhir:
            periode_akhir_str = max_tgl_akhir.strftime('%d-%m-%Y')

    total_angka_kredit = sum(ak.jumlah_angka_kredit for ak in ak_list_for_report if hasattr(ak, 'jumlah_angka_kredit'))

    for ak_item in ak_list_for_report:
        if hasattr(ak_item, 'tanggal_awal_penilaian') and ak_item.tanggal_awal_penilaian and hasattr(ak_item, 'tanggal_akhir_penilaian') and ak_item.tanggal_akhir_penilaian:
            rdelta = relativedelta(ak_item.tanggal_akhir_penilaian, ak_item.tanggal_awal_penilaian)
            months = rdelta.years * 12 + rdelta.months
            if rdelta.days > 0: months += 1
            if months == 0: months = 1
            ak_item.periode_bulan = months
        elif isinstance(ak_item, dict):
            ak_item['periode_bulan'] = 0
        else:
            ak_item.periode_bulan = 0


    if include_integrasi_filter:
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        if angka_integrasi_obj:
            angka_integrasi_value = angka_integrasi_obj.jumlah_angka_integrasi
            total_angka_kredit += angka_integrasi_value
            integrasi_ak_item_display = {
                'penilaian': 'AK Integrasi',
                'jumlah_angka_kredit': angka_integrasi_value,
                'is_integrasi_item': True,
                'periode_bulan': None,
            }
            ak_list_for_report.insert(0, integrasi_ak_item_display)

    # Handle Ak Pendidikan
    if include_pendidikan_filter:
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)
        if ak_pendidikan_records.exists():
            ak_pendidikan_total = sum([ak_pend.jumlah_angka_kredit for ak_pend in ak_pendidikan_records])
            total_angka_kredit += ak_pendidikan_total
            pendidikan_ak_item_display = {
                'penilaian': 'AK Pendidikan',
                'jumlah_angka_kredit': ak_pendidikan_total,
                'is_pendidikan_item': True,
                'periode_bulan': None,
            }
            # Insert after integrasi if present, otherwise at the beginning
            insert_index = 1 if include_integrasi_filter and angka_integrasi_obj else 0
            ak_list_for_report.insert(insert_index, pendidikan_ak_item_display)

    return {
        'pegawai': pegawai,
        'ak_list': ak_list_for_report,
        'tahun': tahun,
        'nama_instansi': latest_ak.instansi.nama_instansi if latest_ak else '',
        'periode_awal_str': periode_awal_str,
        'periode_akhir_str': periode_akhir_str,
        'jabatan_dan_tmt': jabatan_dan_tmt,
        'total_angka_kredit': total_angka_kredit,
        'tempat_ditetapkan': latest_ak.tempat_ditetapkan if latest_ak else '',
        'tanggal_ditetapkan': latest_ak.tanggal_ditetapkan if latest_ak else datetime.now().date(),
        'nama_penilai': latest_ak.penilai.nama if latest_ak and latest_ak.penilai else '',
        'nip_penilai': latest_ak.penilai.nip if latest_ak and latest_ak.penilai else '',
        'pangkat_penilai': latest_ak.penilai.pangkat if latest_ak and latest_ak.penilai else '',
        'golongan_penilai': latest_ak.penilai.golongan if latest_ak and latest_ak.penilai else '',
    }
def _get_penetapan_report_data(pegawai, selected_ak_ids, include_integrasi_filter, include_pendidikan_filter=False):
    ak_records_queryset = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')

    if selected_ak_ids:
        ak_records_filtered = ak_records_queryset.filter(id__in=selected_ak_ids)
    else:
        ak_records_filtered = ak_records_queryset.all()

    latest_ak_unfiltered = AK.objects.filter(pegawai=pegawai).order_by('tanggal_akhir_penilaian').last()
    latest_ak = ak_records_filtered.last() if ak_records_filtered.exists() else None

    tahun = datetime.now().year
    if latest_ak_unfiltered and latest_ak_unfiltered.tanggal_akhir_penilaian:
        tahun = latest_ak_unfiltered.tanggal_akhir_penilaian.year
    elif latest_ak_unfiltered and latest_ak_unfiltered.tanggal_ditetapkan:
        tahun = latest_ak_unfiltered.tanggal_ditetapkan.year

    # === NORMALISASI GOLONGAN ===
    raw_golongan = str(pegawai.golongan).strip()
    alt_map = {
        "IIIA": "III/a",
        "IIIB": "III/b",
        "IIIC": "III/c",
        "IIID": "III/d",
        "3A": "III/a",
        "3B": "III/b",
        "3C": "III/c",
        "3D": "III/d",
        "3a": "III/a",
        "3b": "III/b",
        "3c": "III/c",
        "3d": "III/d",
    }
    golongan = alt_map.get(raw_golongan.upper(), raw_golongan)

    total_lama = GOLONGAN_TO_LAMA.get(golongan, 0.0)

    ak_list_for_report = list(ak_records_filtered)
    total_baru = sum(ak.jumlah_angka_kredit for ak in ak_list_for_report)

    # Tambahkan integrasi jika diminta
    if include_integrasi_filter:
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        if angka_integrasi_obj:
            integrasi_value = angka_integrasi_obj.jumlah_angka_integrasi
            total_baru += integrasi_value
            integrasi_item = {
                'penilaian': 'AK Integrasi',
                'jumlah_angka_kredit': integrasi_value,
                'is_integrasi_item': True
            }
            ak_list_for_report.insert(0, integrasi_item)

    # Tambahkan pendidikan jika diminta
    ak_pendidikan_total = 0
    if include_pendidikan_filter:
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)
        if ak_pendidikan_records.exists():
            ak_pendidikan_total = sum([ak_pend.jumlah_angka_kredit for ak_pend in ak_pendidikan_records])
            # NOTE: For penetapan report, pendidikan is shown in a separate row, not added to total_baru
            pendidikan_item = {
                'penilaian': 'AK Pendidikan',
                'jumlah_angka_kredit': ak_pendidikan_total,
                'is_pendidikan_item': True
            }
            # Insert after integrasi if present, otherwise at the beginning
            insert_index = 1 if include_integrasi_filter and AngkaIntegrasi.objects.filter(pegawai=pegawai).exists() else 0
            ak_list_for_report.insert(insert_index, pendidikan_item)

    # === TERAPKAN PENGURANGAN SESUAI GOLONGAN ===
    PENGURANGAN_GOLONGAN = {
        "III/a": 0,
        "III/b": 50,
        "III/c": 0,
        "III/d": 100,
    }
    pengurangan = PENGURANGAN_GOLONGAN.get(golongan, 0)
    total_baru = max(0.0, total_baru - pengurangan)  # Hindari nilai negatif

    # For penetapan report, total_jumlah includes ak_pendidikan_total if included
    total_jumlah = total_lama + total_baru + (ak_pendidikan_total if include_pendidikan_filter else 0)

    # Hitung kenaikan pangkat
    next_golongan = "N/A"
    pangkat_minimal, jenjang_minimal = 0.0, 0.0
    if golongan in GOLONGAN_HIERARKI:
        idx = GOLONGAN_HIERARKI.index(golongan)
        if idx < len(GOLONGAN_HIERARKI) - 1:
            next_golongan = GOLONGAN_HIERARKI[idx + 1]
            key = (golongan, next_golongan)
            if key in MINIMAL_AK_MAPPING:
                pangkat_minimal, jenjang_minimal = MINIMAL_AK_MAPPING[key]
        else:
            next_golongan = "Tertinggi"

    PANGKAT_OPTIONS_REVERSE = {v: k for k, v in PANGKAT_OPTIONS.items()}
    if next_golongan in GOLONGAN_HIERARKI:
        nama_pangkat_tujuan = PANGKAT_OPTIONS_REVERSE.get(next_golongan, next_golongan)
        teks_tujuan = f"{nama_pangkat_tujuan} {next_golongan}"
    else:
        teks_tujuan = next_golongan

    jenjang_raw = latest_ak_unfiltered.jenjang if latest_ak_unfiltered else ""
    # Use the actual job title from the employee record instead of defaulting to "Analis"
    tmt_jabatan_str = pegawai.tmt_jabatan.strftime('%d-%m-%Y') if pegawai.tmt_jabatan else ""
    jabatan_dan_tmt = f"{pegawai.jabatan} / {tmt_jabatan_str}" if tmt_jabatan_str else pegawai.jabatan
    
    periode_awal_str, periode_akhir_str = '', ''
    if ak_list_for_report:
        ak_models_only = [ak for ak in ak_list_for_report if isinstance(ak, AK)]
        if ak_models_only:
            min_tgl_awal = min((ak.tanggal_awal_penilaian for ak in ak_models_only if ak.tanggal_awal_penilaian), default=None)
            max_tgl_akhir = max((ak.tanggal_akhir_penilaian for ak in ak_models_only if ak.tanggal_akhir_penilaian), default=None)
            if min_tgl_awal:
                periode_awal_str = min_tgl_awal.strftime('%d-%m-%Y')
            if max_tgl_akhir:
                periode_akhir_str = max_tgl_akhir.strftime('%d-%m-%Y')
    
    return {
        'pegawai': pegawai,
        'ak_list': ak_list_for_report,
        'tahun': tahun,
        'nama_instansi': latest_ak_unfiltered.instansi.nama_instansi if latest_ak_unfiltered and latest_ak_unfiltered.instansi else '',
        'periode_awal_str': periode_awal_str,
        'periode_akhir_str': periode_akhir_str,
        'jabatan_dan_tmt': jabatan_dan_tmt,
        'total_lama': total_lama,
        'total_baru': total_baru,          # <-- SUDAH DIKURANGI SESUAI ATURAN
        'total_jumlah': total_jumlah,
        'ak_pendidikan_value': ak_pendidikan_total if include_pendidikan_filter else 0,
        'total_performance_only': total_lama + total_baru,
        'total_baru_with_pendidikan': total_baru + (ak_pendidikan_total if include_pendidikan_filter else 0),
        'pangkat_minimal': pangkat_minimal,
        'jenjang_minimal': jenjang_minimal,
        'hasil_pangkat': total_jumlah - pangkat_minimal,
        'hasil_jenjang': total_jumlah - jenjang_minimal,
        'teks_tujuan': teks_tujuan,
        'tempat_ditetapkan': latest_ak_unfiltered.tempat_ditetapkan if latest_ak_unfiltered else '',
        'tanggal_ditetapkan': latest_ak_unfiltered.tanggal_ditetapkan if latest_ak_unfiltered else datetime.now().date(),
        'nama_penilai': latest_ak_unfiltered.penilai.nama if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
        'nip_penilai': latest_ak_unfiltered.penilai.nip if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
        'pangkat_penilai': latest_ak_unfiltered.penilai.pangkat if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
        'golongan_penilai': latest_ak_unfiltered.penilai.golongan if latest_ak_unfiltered and latest_ak_unfiltered.penilai else '',
    }

def merge_report_view(request):
    pegawai_options = Pegawai.objects.all()
    report_data = {}
    report_generated = False
    all_ak_records_for_pegawai = []
    angka_integrasi_obj = None
    ak_pendidikan_records = []

    pegawai_id = request.POST.get('pegawai_id') or request.GET.get('pegawai_id')
    selected_periods = request.POST.getlist('selected_periods')
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')

    start_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    end_date = None
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # This is for retaining the state in the template
    selected_ak_ids_int = []
    include_angka_integrasi_from_post = False
    include_ak_pendidikan_from_post = False
    for p_id in selected_periods:
        if p_id == 'integrasi_ak':
            include_angka_integrasi_from_post = True
        elif p_id == 'pendidikan_ak':
            include_ak_pendidikan_from_post = True
        else:
            try:
                selected_ak_ids_int.append(int(p_id))
            except ValueError:
                pass

    if pegawai_id:
        pegawai = get_object_or_404(Pegawai, id=pegawai_id)
        all_ak_records_for_pegawai = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)

        if start_date and end_date:
            all_ak_records_for_pegawai = all_ak_records_for_pegawai.filter(
                tanggal_awal_penilaian__gte=start_date,
                tanggal_akhir_penilaian__lte=end_date
            )

        if request.method == 'POST' and 'generate_report' in request.POST:

            final_period_ids = selected_ak_ids_int
            include_integrasi = include_angka_integrasi_from_post
            include_pendidikan = include_ak_pendidikan_from_post

            # If nothing is selected, use all
            if not selected_periods:
                final_period_ids = [ak.id for ak in all_ak_records_for_pegawai]
                if angka_integrasi_obj:
                    include_integrasi = True
                if ak_pendidikan_records.exists():
                    include_pendidikan = True

            konversi_report_data, konversi_ak_list = _get_konversi_report_data(pegawai, final_period_ids, include_integrasi, include_pendidikan)
            akumulasi_data = _get_akumulasi_report_data(pegawai, final_period_ids, include_integrasi, include_pendidikan)
            penetapan_data = _get_penetapan_report_data(pegawai, final_period_ids, include_integrasi, include_pendidikan)

            report_data = {
                'konversi': {
                    'report_data': konversi_report_data,
                    'ak_list': konversi_ak_list
                },
                'akumulasi': akumulasi_data,
                'penetapan': penetapan_data,
                'pegawai': pegawai,
            }
            report_generated = True

    # For template context
    selected_ids_for_template = [str(i) for i in selected_ak_ids_int]
    if include_angka_integrasi_from_post:
        selected_ids_for_template.append('integrasi_ak')
    if include_ak_pendidikan_from_post:
        selected_ids_for_template.append('pendidikan_ak')

    context = {
        'pegawai_options': pegawai_options,
        'report_generated': report_generated,
        'report_data': report_data,
        'selected_pegawai_id': int(pegawai_id) if pegawai_id else None,
        'all_ak_records': all_ak_records_for_pegawai,
        'ak_pendidikan_records': ak_pendidikan_records,
        'angka_integrasi_obj': angka_integrasi_obj,
        'selected_periods': selected_ids_for_template,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'pegawai/merge_report.html', context)


def merge_report_pdf_view(request):
    pegawai_id = request.GET.get('pegawai_id')
    if not pegawai_id:
        return HttpResponse("Pegawai ID is required.", status=400)

    selected_periods = request.GET.getlist('selected_periods')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    end_date = None
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Process selected periods
    selected_ak_ids_int = []
    include_angka_integrasi = False
    include_ak_pendidikan = False
    for p_id in selected_periods:
        if p_id == 'integrasi_ak':
            include_angka_integrasi = True
        elif p_id == 'pendidikan_ak':
            include_ak_pendidikan = True
        else:
            try:
                selected_ak_ids_int.append(int(p_id))
            except ValueError:
                pass

    pegawai = get_object_or_404(Pegawai, id=pegawai_id)

    # Get all AK records for the selected pegawai
    all_ak_records_for_pegawai = AK.objects.filter(pegawai=pegawai).order_by('tanggal_awal_penilaian')

    # Apply date filters if provided
    if start_date and end_date:
        all_ak_records_for_pegawai = all_ak_records_for_pegawai.filter(
            tanggal_awal_penilaian__gte=start_date,
            tanggal_akhir_penilaian__lte=end_date
        )

    # Determine final period IDs
    final_period_ids = selected_ak_ids_int
    include_integrasi = include_angka_integrasi
    include_pendidikan = include_ak_pendidikan

    # If nothing is selected, use all
    if not selected_periods:
        final_period_ids = [ak.id for ak in all_ak_records_for_pegawai]
        angka_integrasi_obj = AngkaIntegrasi.objects.filter(pegawai=pegawai).first()
        ak_pendidikan_records = AkPendidikan.objects.filter(pegawai=pegawai)
        if angka_integrasi_obj:
            include_integrasi = True
        if ak_pendidikan_records.exists():
            include_pendidikan = True

    # Generate data for all three reports
    konversi_report_data, konversi_ak_list = _get_konversi_report_data(pegawai, final_period_ids, include_integrasi, include_pendidikan)
    akumulasi_data = _get_akumulasi_report_data(pegawai, final_period_ids, include_integrasi, include_pendidikan)
    penetapan_data = _get_penetapan_report_data(pegawai, final_period_ids, include_integrasi, include_pendidikan)

    report_data = {
        'konversi': {
            'report_data': konversi_report_data,
            'ak_list': konversi_ak_list
        },
        'akumulasi': akumulasi_data,
        'penetapan': penetapan_data,
        'pegawai': pegawai,
    }

    context = {
        'report_data': report_data,
        'base_dir': settings.BASE_DIR,
    }

    # Use a separate template for the PDF version to avoid Font Awesome icons
    pdf = render_to_pdf('pegawai/merge_report_pdf_template.html', context)
    if pdf:
        # The render_to_pdf function already returns an HttpResponse with proper PDF content
        return pdf
    return HttpResponse("Error generating PDF", status=500)

