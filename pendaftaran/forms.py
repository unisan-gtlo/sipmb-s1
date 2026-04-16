from django import forms
from .models import ProfilPendaftar


class ProfilDiriForm(forms.ModelForm):
    class Meta:
        model  = ProfilPendaftar
        fields = [
            'nik', 'tempat_lahir', 'tgl_lahir', 'jenis_kelamin',
            'agama', 'kewarganegaraan', 'status_nikah', 'kebutuhan_khusus',
            'alamat_lengkap', 'provinsi', 'kabupaten_kota',
            'kecamatan', 'kelurahan', 'kode_pos',
        ]
        widgets = {
            'nik': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '16 digit NIK',
                'maxlength': '16',
            }),
            'tempat_lahir': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kota/kabupaten tempat lahir',
            }),
            'tgl_lahir': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'jenis_kelamin': forms.Select(attrs={'class': 'form-select'}),
            'agama': forms.Select(attrs={'class': 'form-select'}),
            'kewarganegaraan': forms.Select(attrs={'class': 'form-select'}),
            'status_nikah': forms.Select(attrs={'class': 'form-select'}),
            'kebutuhan_khusus': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Isi jika difabel, kosongkan jika tidak',
            }),
            'alamat_lengkap': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Alamat domisili lengkap',
            }),
            'provinsi': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Provinsi',
            }),
            'kabupaten_kota': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kabupaten / Kota',
            }),
            'kecamatan': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kecamatan',
            }),
            'kelurahan': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kelurahan / Desa',
            }),
            'kode_pos': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kode pos',
            }),
        }

    def clean_nik(self):
        nik = self.cleaned_data.get('nik', '').strip()
        if nik and len(nik) != 16:
            raise forms.ValidationError('NIK harus 16 digit.')
        if nik and not nik.isdigit():
            raise forms.ValidationError('NIK hanya boleh angka.')
        return nik


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
    class Meta:
        model  = ProfilPendaftar
        fields = [
            'asal_sekolah', 'jurusan_sekolah', 'tahun_lulus',
            'no_ijazah', 'nilai_rata_rata', 'prestasi',
        ]
        widgets = {
            'asal_sekolah': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Nama SMA / SMK / MA asal',
            }),
            'jurusan_sekolah': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Jurusan di sekolah (IPA, IPS, TKJ, dll)',
            }),
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
                'placeholder': 'Prestasi akademik / non-akademik yang pernah diraih (opsional)',
            }),
        }


class ProfilFotoForm(forms.ModelForm):
    class Meta:
        model  = ProfilPendaftar
        fields = ['foto']
        widgets = {
            'foto': forms.FileInput(attrs={
                'class': 'form-control', 'accept': 'image/*',
            }),
        }