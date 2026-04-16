from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import ProfilPendaftar
from utils.simda_reader import get_provinsi, get_jurusan_sekolah, get_agama
from master.models import JalurPenerimaan, GelombangPenerimaan, ProdiPMB



class ProfilDiriForm(forms.ModelForm):

    # Field wilayah — pakai ID dari SIMDA
    provinsi_id = forms.ChoiceField(
        choices=[('', '-- Pilih Provinsi --')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_provinsi'})
    )
    kabupaten_kota_id = forms.ChoiceField(
        choices=[('', '-- Pilih Kabupaten/Kota --')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_kabupaten_kota'})
    )
    kecamatan_id = forms.ChoiceField(
        choices=[('', '-- Pilih Kecamatan --')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_kecamatan'})
    )

    # Field agama dari SIMDA
    agama_id = forms.ChoiceField(
        choices=[('', '-- Pilih Agama --')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Sumber informasi
    sumber_informasi = forms.ChoiceField(
        choices=[('', '-- Darimana Anda tahu tentang UNISAN? --')] + ProfilPendaftar.SUMBER_INFO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

   
    class Meta:
        model  = ProfilPendaftar
        fields = [
            'nik', 'tempat_lahir', 'tgl_lahir', 'jenis_kelamin',
            'agama_id', 'agama_nama', 'kewarganegaraan', 'status_nikah',
            'kebutuhan_khusus', 'foto',
            'alamat_lengkap',
            'provinsi_id', 'provinsi_nama',
            'kabupaten_kota_id', 'kabupaten_kota_nama',
            'kecamatan_id', 'kecamatan_nama',
            'kelurahan', 'kode_pos',
            'sumber_informasi', 'sumber_informasi_lain',
        ]
        widgets = {
            'nik': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '16 digit NIK', 'maxlength': '16',
            }),
            'tempat_lahir': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kota/kabupaten tempat lahir',
            }),
            'tgl_lahir': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'jenis_kelamin': forms.Select(attrs={'class': 'form-select'}),
            'agama_nama': forms.HiddenInput(),
            'kewarganegaraan': forms.Select(attrs={'class': 'form-select'}),
            'status_nikah': forms.Select(attrs={'class': 'form-select'}),
            'kebutuhan_khusus': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Isi jika difabel, kosongkan jika tidak',
            }),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'alamat_lengkap': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3, 'placeholder': 'Alamat domisili lengkap',
            }),
            'provinsi_nama': forms.HiddenInput(),
            'kabupaten_kota_nama': forms.HiddenInput(),
            'kecamatan_nama': forms.HiddenInput(),
            'kelurahan': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kelurahan / Desa',
            }),
            'kode_pos': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kode pos',
            }),
            'sumber_informasi_lain': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Sebutkan sumber informasi lainnya',
            }),
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load provinsi dari SIMDA
        try:
            provinsi_list = get_provinsi()
            self.fields['provinsi_id'].choices = (
                [('', '-- Pilih Provinsi --')] +
                [(str(p['id']), p['nama']) for p in provinsi_list]
            )
            agama_list = get_agama()
            self.fields['agama_id'].choices = (
                [('', '-- Pilih Agama --')] +
                [(str(a['id']), a['nama']) for a in agama_list]
            )
           
        except Exception:
            pass

        # Jika sudah ada data, set nilai awal dropdown
        if self.instance and self.instance.pk:
            if self.instance.provinsi_id:
                self.fields['provinsi_id'].initial = str(self.instance.provinsi_id)
            if self.instance.kabupaten_kota_id:
                self.fields['kabupaten_kota_id'].initial = str(self.instance.kabupaten_kota_id)
                # Load kab/kota untuk provinsi yang dipilih
                from utils.simda_reader import get_kabupaten_kota
                kab_list = get_kabupaten_kota(provinsi_id=self.instance.provinsi_id)
                self.fields['kabupaten_kota_id'].choices = (
                    [('', '-- Pilih Kabupaten/Kota --')] +
                    [(str(k['id']), k['nama']) for k in kab_list]
                )
            if self.instance.kecamatan_id:
                self.fields['kecamatan_id'].initial = str(self.instance.kecamatan_id)
                from utils.simda_reader import get_kecamatan
                kec_list = get_kecamatan(kabupaten_kota_id=self.instance.kabupaten_kota_id)
                self.fields['kecamatan_id'].choices = (
                    [('', '-- Pilih Kecamatan --')] +
                    [(str(k['id']), k['nama']) for k in kec_list]
                )
            if self.instance.agama_id:
                self.fields['agama_id'].initial = str(self.instance.agama_id)

    def clean_nik(self):
        nik = self.cleaned_data.get('nik', '').strip()
        if nik and len(nik) != 16:
            raise forms.ValidationError('NIK harus 16 digit.')
        if nik and not nik.isdigit():
            raise forms.ValidationError('NIK hanya boleh angka.')
        return nik

    def clean(self):
        cleaned = super().clean()
        # Simpan nama wilayah dari SIMDA ke field nama
        try:
            from utils.simda_reader import get_provinsi, get_kabupaten_kota, get_kecamatan, get_agama
            prov_id = cleaned.get('provinsi_id')
            kab_id  = cleaned.get('kabupaten_kota_id')
            kec_id  = cleaned.get('kecamatan_id')
            agama_id = cleaned.get('agama_id')

            if prov_id:
                cleaned['provinsi_id'] = int(prov_id)
                provs = get_provinsi()
                prov  = next((p for p in provs if str(p['id']) == str(prov_id)), None)
                if prov:
                    cleaned['provinsi_nama'] = prov['nama']

            if kab_id:
                cleaned['kabupaten_kota_id'] = int(kab_id)
                kabs = get_kabupaten_kota(provinsi_id=prov_id)
                kab  = next((k for k in kabs if str(k['id']) == str(kab_id)), None)
                if kab:
                    cleaned['kabupaten_kota_nama'] = kab['nama']

            if kec_id:
                cleaned['kecamatan_id'] = int(kec_id)
                kecs = get_kecamatan(kabupaten_kota_id=kab_id)
                kec  = next((k for k in kecs if str(k['id']) == str(kec_id)), None)
                if kec:
                    cleaned['kecamatan_nama'] = kec['nama']

            if agama_id:
                cleaned['agama_id'] = int(agama_id)
                agamas = get_agama()
                agama  = next((a for a in agamas if str(a['id']) == str(agama_id)), None)
                if agama:
                    cleaned['agama_nama'] = agama['nama']
        except Exception:
            pass
        return cleaned

class ProfilOrtuForm(forms.ModelForm):
    class Meta:
        model  = ProfilPendaftar
        fields = [
            'nama_ayah', 'pekerjaan_ayah', 'penghasilan_ayah',
            'nama_ibu', 'pekerjaan_ibu', 'penghasilan_ibu',
            'nama_wali', 'no_hp_ortu', 'alamat_ortu',
        ]
        widgets = {
            'nama_ayah': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nama lengkap ayah kandung',
            }),
            'pekerjaan_ayah': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Pekerjaan ayah',
            }),
            'penghasilan_ayah': forms.Select(
                choices=[
                    ('', '-- Pilih Range Penghasilan --'),
                    ('< 1jt',    'Di bawah Rp 1.000.000'),
                    ('1-3jt',   'Rp 1.000.000 – Rp 3.000.000'),
                    ('3-5jt',   'Rp 3.000.000 – Rp 5.000.000'),
                    ('5-10jt',  'Rp 5.000.000 – Rp 10.000.000'),
                    ('> 10jt',  'Di atas Rp 10.000.000'),
                ],
                attrs={'class': 'form-select'}
            ),
            'nama_ibu': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nama lengkap ibu kandung',
            }),
            'pekerjaan_ibu': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Pekerjaan ibu',
            }),
            'penghasilan_ibu': forms.Select(
                choices=[
                    ('', '-- Pilih Range Penghasilan --'),
                    ('< 1jt',    'Di bawah Rp 1.000.000'),
                    ('1-3jt',   'Rp 1.000.000 – Rp 3.000.000'),
                    ('3-5jt',   'Rp 3.000.000 – Rp 5.000.000'),
                    ('5-10jt',  'Rp 5.000.000 – Rp 10.000.000'),
                    ('> 10jt',  'Di atas Rp 10.000.000'),
                ],
                attrs={'class': 'form-select'}
            ),
            'nama_wali': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama wali (isi jika bukan orang tua)',
            }),
            'no_hp_ortu': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nomor HP orang tua / wali aktif',
            }),
            'alamat_ortu': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Alamat orang tua / wali (kosongkan jika sama dengan alamat Anda)',
            }),
        }


class ProfilPendidikanForm(forms.ModelForm):

    # Filter lokasi sekolah
    sekolah_provinsi_id = forms.ChoiceField(
        choices=[('', '-- Provinsi asal sekolah --')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_sekolah_provinsi'})
    )
    sekolah_nama_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ketik nama sekolah (min 3 huruf)...',
            'id': 'id_sekolah_nama_input',
            'autocomplete': 'off',
        })
    )
    jurusan_id = forms.ChoiceField(
        choices=[('', '-- Pilih Jurusan --')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_jurusan'})
    )

    class Meta:
        model  = ProfilPendaftar
        fields = [
            'sekolah_id', 'asal_sekolah', 'npsn',
            'jurusan_id', 'jurusan_sekolah',
            'tahun_lulus', 'no_ijazah', 'nilai_rata_rata', 'prestasi',
        ]
        widgets = {
            'sekolah_id':    forms.HiddenInput(),
            'asal_sekolah':  forms.HiddenInput(),
            'npsn':          forms.HiddenInput(),
            'jurusan_sekolah': forms.HiddenInput(),
            'tahun_lulus': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Tahun kelulusan (cth: 2024)',
                'min': '2000', 'max': '2030',
            }),
            'no_ijazah': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nomor seri ijazah',
            }),
            'nilai_rata_rata': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Nilai rata-rata (cth: 85.50)',
                'step': '0.01', 'min': '0', 'max': '100',
            }),
            'prestasi': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Prestasi akademik/non-akademik (opsional)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from utils.simda_reader import get_provinsi, get_jurusan_sekolah
            provinsi_list = get_provinsi()
            self.fields['sekolah_provinsi_id'].choices = (
                [('', '-- Provinsi asal sekolah --')] +
                [(str(p['id']), p['nama']) for p in provinsi_list]
            )
            jurusan_list = get_jurusan_sekolah()
            self.fields['jurusan_id'].choices = (
                [('', '-- Pilih Jurusan --')] +
                [(str(j['id']), j['nama']) for j in jurusan_list]
            )
        except Exception:
            pass

        # Set nilai awal jika sudah ada data
        if self.instance and self.instance.pk:
            if self.instance.asal_sekolah:
                self.fields['sekolah_nama_input'].initial = self.instance.asal_sekolah
            if self.instance.jurusan_id:
                self.fields['jurusan_id'].initial = self.instance.jurusan_id

class ProfilFotoForm(forms.ModelForm):
    class Meta:
        model  = ProfilPendaftar

        fields = ['foto']
        widgets = {
            'foto': forms.FileInput(attrs={
                'class': 'form-control', 'accept': 'image/*',
            }),
        }