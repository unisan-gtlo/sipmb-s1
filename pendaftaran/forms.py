from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import ProfilPendaftar
from utils.simda_reader import get_provinsi, get_jurusan_sekolah, get_agama
from master.models import JalurPenerimaan, GelombangPenerimaan, ProdiPMB


class ProfilDiriForm(forms.ModelForm):

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
    agama_id = forms.ChoiceField(
        choices=[('', '-- Pilih Agama --')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
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
            'kebutuhan_khusus', 'ukuran_baju',
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
            'tgl_lahir': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                }
            ),
            'jenis_kelamin':  forms.Select(attrs={'class': 'form-select'}),
            'agama_nama':     forms.HiddenInput(),
            'kewarganegaraan': forms.Select(attrs={'class': 'form-select'}),
            'status_nikah':   forms.Select(attrs={'class': 'form-select'}),
            'kebutuhan_khusus': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Isi jika difabel, kosongkan jika tidak',
            }),
            'ukuran_baju':    forms.Select(attrs={'class': 'form-select'}),
            'alamat_lengkap': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Alamat domisili lengkap',
            }),
            'provinsi_nama':       forms.HiddenInput(),
            'kabupaten_kota_nama': forms.HiddenInput(),
            'kecamatan_nama':      forms.HiddenInput(),
            'kelurahan': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kelurahan / Desa',
            }),
            'kode_pos': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Kode pos',
            }),
            'sumber_informasi_lain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sebutkan sumber informasi lainnya',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ----- Isi choices provinsi & agama (selalu) -----
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

        # ----- Tentukan provinsi_id & kabupaten_kota_id yang dipakai -----
        # Prioritas: (1) data POST → (2) data instance yang ada
        from utils.simda_reader import get_kabupaten_kota, get_kecamatan

        prov_id = None
        kab_id  = None

        if self.is_bound and self.data:
            # Saat POST: ambil dari data yang di-submit browser
            prov_id = self.data.get('provinsi_id') or None
            kab_id  = self.data.get('kabupaten_kota_id') or None
        elif self.instance and self.instance.pk:
            # Saat GET / render ulang: ambil dari instance yang ada
            prov_id = self.instance.provinsi_id
            kab_id  = self.instance.kabupaten_kota_id

        # ----- Isi choices kabupaten/kota sesuai provinsi terpilih -----
        if prov_id:
            try:
                kab_list = get_kabupaten_kota(provinsi_id=int(prov_id))
                self.fields['kabupaten_kota_id'].choices = (
                    [('', '-- Pilih Kabupaten/Kota --')] +
                    [(str(k['id']), k['nama']) for k in kab_list]
                )
            except Exception:
                pass

        # ----- Isi choices kecamatan sesuai kab/kota terpilih -----
        if kab_id:
            try:
                kec_list = get_kecamatan(kabupaten_kota_id=int(kab_id))
                self.fields['kecamatan_id'].choices = (
                    [('', '-- Pilih Kecamatan --')] +
                    [(str(k['id']), k['nama']) for k in kec_list]
                )
            except Exception:
                pass

        # ----- Set nilai awal (initial) dari instance untuk render GET -----
        if self.instance and self.instance.pk:
            if self.instance.provinsi_id:
                self.fields['provinsi_id'].initial = str(self.instance.provinsi_id)
            if self.instance.kabupaten_kota_id:
                self.fields['kabupaten_kota_id'].initial = str(self.instance.kabupaten_kota_id)
            if self.instance.kecamatan_id:
                self.fields['kecamatan_id'].initial = str(self.instance.kecamatan_id)
            if self.instance.agama_id:
                self.fields['agama_id'].initial = str(self.instance.agama_id)

    def clean_nik(self):
        nik = self.cleaned_data.get('nik', '').strip()
        if nik and len(nik) != 16:
            raise forms.ValidationError('NIK harus 16 digit.')
        if nik and not nik.isdigit():
            raise forms.ValidationError('NIK hanya boleh angka.')
        return nik
    def save(self, commit=True):
        """
        Override save: pastikan 4 field ID (provinsi, kab/kota, kecamatan, agama)
        ter-assign ke instance, karena Django ModelForm tidak auto-map
        ChoiceField custom ke BigIntegerField di model.
        """
        instance = super().save(commit=False)
        cleaned = self.cleaned_data

        # Paksa assign ID dari cleaned_data ke instance
        instance.provinsi_id       = cleaned.get('provinsi_id') or None
        instance.kabupaten_kota_id = cleaned.get('kabupaten_kota_id') or None
        instance.kecamatan_id      = cleaned.get('kecamatan_id') or None
        instance.agama_id          = cleaned.get('agama_id') or None

        # Pastikan nama wilayah juga ter-assign (hasil dari clean())
        instance.provinsi_nama       = cleaned.get('provinsi_nama', '') or ''
        instance.kabupaten_kota_nama = cleaned.get('kabupaten_kota_nama', '') or ''
        instance.kecamatan_nama      = cleaned.get('kecamatan_nama', '') or ''
        instance.agama_nama          = cleaned.get('agama_nama', '') or ''

        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned = super().clean()
        try:
            from utils.simda_reader import (get_provinsi, get_kabupaten_kota,
                                             get_kecamatan, get_agama)
            prov_id  = cleaned.get('provinsi_id')
            kab_id   = cleaned.get('kabupaten_kota_id')
            kec_id   = cleaned.get('kecamatan_id')
            agama_id = cleaned.get('agama_id')

            if prov_id:
                cleaned['provinsi_id'] = int(prov_id)
                provs = get_provinsi()
                prov  = next((p for p in provs if str(p['id']) == str(prov_id)), None)
                if prov:
                    cleaned['provinsi_nama'] = prov['nama']

            if kab_id:
                cleaned['kabupaten_kota_id'] = int(kab_id)
                # FIX: pakai int(prov_id) bukan prov_id string
                kabs = get_kabupaten_kota(provinsi_id=int(prov_id) if prov_id else None)
                kab  = next((k for k in kabs if str(k['id']) == str(kab_id)), None)
                if kab:
                    cleaned['kabupaten_kota_nama'] = kab['nama']
            else:
                cleaned['kabupaten_kota_id'] = None

            if kec_id:
                cleaned['kecamatan_id'] = int(kec_id)
                # FIX: pakai int(kab_id) bukan string
                kecs = get_kecamatan(
                    kabupaten_kota_id=int(kab_id) if kab_id else None
                )
                kec  = next((k for k in kecs if str(k['id']) == str(kec_id)), None)
                if kec:
                    cleaned['kecamatan_nama'] = kec['nama']
            else:
                cleaned['kecamatan_id'] = None

            if agama_id:
                cleaned['agama_id'] = int(agama_id)
                agamas = get_agama()
                agama  = next(
                    (a for a in agamas if str(a['id']) == str(agama_id)), None
                )
                if agama:
                    cleaned['agama_nama'] = agama['nama']
            else:
                cleaned['agama_id'] = None

        except Exception as e:
            pass
        return cleaned


# ============================================================
# FORM ORANG TUA — tambah pendidikan & no HP terpisah
# ============================================================
class ProfilOrtuForm(forms.ModelForm):

    PENDIDIKAN_CHOICES = [
        ('', '-- Pilih Pendidikan --'),
        ('SD',            'SD / Sederajat'),
        ('SMP',           'SMP / Sederajat'),
        ('SMA',           'SMA / SMK / Sederajat'),
        ('D3',            'Diploma (D1/D2/D3)'),
        ('D4',            'D4 / Sarjana Terapan'),
        ('S1',            'S1 / Sarjana'),
        ('S2',            'S2 / Magister'),
        ('S3',            'S3 / Doktor'),
        ('TIDAK_SEKOLAH', 'Tidak Sekolah'),
    ]

    pendidikan_ayah = forms.ChoiceField(
        choices=PENDIDIKAN_CHOICES,
        required=False,
        label='Pendidikan Terakhir Ayah',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    pendidikan_ibu = forms.ChoiceField(
        choices=PENDIDIKAN_CHOICES,
        required=False,
        label='Pendidikan Terakhir Ibu',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    no_hp_ayah = forms.CharField(
        required=False,
        label='No HP Ayah',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nomor HP aktif ayah'
        })
    )
    no_hp_ibu = forms.CharField(
        required=False,
        label='No HP Ibu',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nomor HP aktif ibu'
        })
    )

    class Meta:
        model  = ProfilPendaftar
        fields = [
            'nama_ayah', 'pekerjaan_ayah', 'pendidikan_ayah', 'penghasilan_ayah', 'no_hp_ayah',
            'nama_ibu',  'pekerjaan_ibu',  'pendidikan_ibu',  'penghasilan_ibu',  'no_hp_ibu',
            'nama_wali', 'no_hp_ortu', 'alamat_ortu',
        ]
        widgets = {
            'nama_ayah': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap ayah kandung',
            }),
            'pekerjaan_ayah': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Pekerjaan ayah',
            }),
            'penghasilan_ayah': forms.Select(
                choices=[
                    ('', '-- Pilih Range Penghasilan --'),
                    ('< 1jt',   'Di bawah Rp 1.000.000'),
                    ('1-3jt',  'Rp 1.000.000 – Rp 3.000.000'),
                    ('3-5jt',  'Rp 3.000.000 – Rp 5.000.000'),
                    ('5-10jt', 'Rp 5.000.000 – Rp 10.000.000'),
                    ('> 10jt', 'Di atas Rp 10.000.000'),
                ],
                attrs={'class': 'form-select'}
            ),
            'nama_ibu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap ibu kandung',
            }),
            'pekerjaan_ibu': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Pekerjaan ibu',
            }),
            'penghasilan_ibu': forms.Select(
                choices=[
                    ('', '-- Pilih Range Penghasilan --'),
                    ('< 1jt',   'Di bawah Rp 1.000.000'),
                    ('1-3jt',  'Rp 1.000.000 – Rp 3.000.000'),
                    ('3-5jt',  'Rp 3.000.000 – Rp 5.000.000'),
                    ('5-10jt', 'Rp 5.000.000 – Rp 10.000.000'),
                    ('> 10jt', 'Di atas Rp 10.000.000'),
                ],
                attrs={'class': 'form-select'}
            ),
            'nama_wali': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama wali (isi jika bukan orang tua)',
            }),
            'no_hp_ortu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'No HP yang bisa dihubungi (wali/ortu)',
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