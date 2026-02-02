from django import forms
from .models import AK, Pegawai, AngkaIntegrasi, Instansi, Penilai, AkPendidikan
from .constants import JENJANG_OPTIONS, PENILAIAN_OPTIONS, PENILAIAN_TO_PROSENTASE, JENJANG_TO_KOEFISIEN

# Helper function to apply form-control class
def apply_form_control(field):
    if hasattr(field.widget, 'attrs'):
        if field.widget.input_type == 'checkbox':
            field.widget.attrs.update({'class': 'form-check-input'})
        else:
            current_class = field.widget.attrs.get('class', '')
            if 'form-control' not in current_class:
                field.widget.attrs['class'] = (current_class + ' form-control').strip()

class AKForm(forms.ModelForm):
    jenjang = forms.ChoiceField(choices=[(j, j) for j in JENJANG_OPTIONS], label="Jenjang")
    penilaian = forms.ChoiceField(choices=[(p, p) for p in PENILAIAN_OPTIONS], label="Penilaian")

    class Meta:
        model = AK
        # Exclude the fields that will be calculated in the view
        exclude = ['prosentase', 'koefisien', 'jumlah_angka_kredit']
        widgets = {
            'tanggal_awal_penilaian': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_akhir_penilaian': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_ditetapkan': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            apply_form_control(field)

class PegawaiForm(forms.ModelForm):
    class Meta:
        model = Pegawai
        fields = '__all__'
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}),
            'tmt_pangkat': forms.DateInput(attrs={'type': 'date'}),
            'tmt_jabatan': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            apply_form_control(field)

class AngkaIntegrasiForm(forms.ModelForm):
    class Meta:
        model = AngkaIntegrasi
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            apply_form_control(field)

class InstansiForm(forms.ModelForm):
    class Meta:
        model = Instansi
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            apply_form_control(field)

class PenilaiForm(forms.ModelForm):
    class Meta:
        model = Penilai
        fields = '__all__'
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}),
            'tmt_pangkat': forms.DateInput(attrs={'type': 'date'}),
            'tmt_jabatan': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            apply_form_control(field)

class AkPendidikanForm(forms.ModelForm):
    class Meta:
        model = AkPendidikan
        fields = '__all__'
        widgets = {
            'tanggal_awal_penilaian': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_akhir_penilaian': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_pelaksanaan': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_ditetapkan': forms.DateInput(attrs={'type': 'date'}),
            'file_sertifikat': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            apply_form_control(field)
            # Add specific validation or help text for certain fields
            if field_name == 'durasi_pelatihan':
                field.help_text = "Durasi pelatihan dalam jam"
            elif field_name == 'nomor_sertifikat':
                field.help_text = "Nomor sertifikat harus unik"