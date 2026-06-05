import csv
import io
from django.http import HttpResponse
from django.template.loader import get_template
from .models import Pegawai
from io import BytesIO
import os

def render_to_pdf(template_src, context_dict=None):
    """
    Render HTML template to PDF using xhtml2pdf
    """
    if context_dict is None:
        context_dict = {}

    try:
        from xhtml2pdf import pisa
    except ImportError as e:
        return HttpResponse(f"xhtml2pdf import error: {e}", status=500)

    try:
        template = get_template(template_src)
        html = template.render(context_dict)
        result = BytesIO()
        pdf = pisa.CreatePDF(html, dest=result, encoding='utf-8')
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        return HttpResponse(f"Error generating PDF: {pdf.err}", status=500)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

def export_pegawai_to_csv():
    """Export all Pegawai data to CSV format."""
    # Create a StringIO buffer to write CSV data
    buffer = io.StringIO()

    # Define the fieldnames based on the Pegawai model
    fieldnames = [
        'id',
        'nama',
        'nip',
        'no_seri_karpeg',
        'tempat_lahir',
        'tanggal_lahir',
        'jenis_kelamin',
        'pangkat',
        'golongan',
        'tmt_pangkat',
        'jabatan',
        'tmt_jabatan',
        'unit_kerja'
    ]

    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    # Write all Pegawai objects to the CSV
    for pegawai in Pegawai.objects.all():
        writer.writerow({
            'id': pegawai.id,
            'nama': pegawai.nama,
            'nip': f'="{pegawai.nip}"',  # Format NIP to prevent Excel from converting to scientific notation
            'no_seri_karpeg': pegawai.no_seri_karpeg,
            'tempat_lahir': pegawai.tempat_lahir,
            'tanggal_lahir': pegawai.tanggal_lahir.strftime('%d-%m-%Y') if pegawai.tanggal_lahir else '',
            'jenis_kelamin': pegawai.jenis_kelamin,
            'pangkat': pegawai.pangkat,
            'golongan': pegawai.golongan,
            'tmt_pangkat': pegawai.tmt_pangkat.strftime('%d-%m-%Y') if pegawai.tmt_pangkat else '',
            'jabatan': pegawai.jabatan,
            'tmt_jabatan': pegawai.tmt_jabatan.strftime('%d-%m-%Y') if pegawai.tmt_jabatan else '',
            'unit_kerja': pegawai.unit_kerja
        })

    # Get the CSV content
    csv_content = buffer.getvalue()
    buffer.close()

    return csv_content

def import_pegawai_from_csv(csv_file):
    """Import Pegawai data from a CSV file."""
    decoded_file = csv_file.read().decode('utf-8-sig')
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)

    imported_count = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
        try:
            # Clean the NIP field to handle various Excel formats
            nip = row['nip']

            # Handle different Excel formats that might appear
            if nip.startswith('="') and nip.endswith('"'):
                nip = nip[2:-1]  # Remove =" and " from the beginning and end
            elif nip.startswith('=') and len(nip) > 1:
                # Handle other Excel formulas like =123456789012345678
                nip = nip[1:]

            # Handle scientific notation (convert back to full number)
            if 'E+' in nip.upper() or 'E-' in nip.upper():
                try:
                    # Convert scientific notation back to full number string
                    nip = str(int(float(nip)))
                except ValueError:
                    # If conversion fails, keep original
                    pass

            # Remove any leading/trailing whitespace
            nip = nip.strip()

            # Convert date strings to date objects if they exist
            tanggal_lahir = None
            if row.get('tanggal_lahir'):
                tanggal_lahir = row['tanggal_lahir']

            tmt_pangkat = None
            if row.get('tmt_pangkat'):
                tmt_pangkat = row['tmt_pangkat']

            tmt_jabatan = None
            if row.get('tmt_jabatan'):
                tmt_jabatan = row['tmt_jabatan']

            # Create or update the Pegawai object
            pegawai, created = Pegawai.objects.update_or_create(
                nip=nip,
                defaults={
                    'nama': row.get('nama', ''),
                    'no_seri_karpeg': row.get('no_seri_karpeg', ''),
                    'tempat_lahir': row.get('tempat_lahir', ''),
                    'tanggal_lahir': tanggal_lahir,
                    'jenis_kelamin': row.get('jenis_kelamin', ''),
                    'pangkat': row.get('pangkat', ''),
                    'golongan': row.get('golongan', ''),
                    'tmt_pangkat': tmt_pangkat,
                    'jabatan': row.get('jabatan', ''),
                    'tmt_jabatan': tmt_jabatan,
                    'unit_kerja': row.get('unit_kerja', '')
                }
            )
            imported_count += 1

        except Exception as e:
            errors.append(f"Row {row_num}: Error importing - {str(e)}")

    return imported_count, errors