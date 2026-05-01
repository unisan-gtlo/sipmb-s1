"""
Forms khusus untuk admin/operator PMB.

Di-isolate dari forms maba (pendaftaran/forms.py) supaya:
- Bisa custom field per kebutuhan operator (subset atau extension)
- Bisa tambah field operator-only seperti 'alasan_edit' (audit trail)
- Tidak ganggu form maba kalau ada perubahan
"""
# ============================================================================
# CONSTANTS — Choices untuk dropdown
# ============================================================================

JENIS_KELAMIN_CHOICES = [
    ('', '-- Pilih Jenis Kelamin --'),
    ('L', 'Laki-laki'),
    ('P', 'Perempuan'),
]

KEWARGANEGARAAN_CHOICES = [
    ('WNI', 'WNI - Warga Negara Indonesia'),
    ('WNA', 'WNA - Warga Negara Asing'),
]

STATUS_NIKAH_CHOICES = [
    ('belum_menikah', 'Belum Menikah'),
    ('menikah', 'Menikah'),
    ('cerai', 'Cerai'),
]

from django import forms
from pendaftaran.models import ProfilPendaftar
from pendaftaran.forms import PEKERJAAN_CHOICES
from accounts.utils import normalisasi_nama

class OperatorEditDataDiriForm(forms.ModelForm):
    """
    Form untuk operator/admin PMB edit data diri & alamat pendaftar.
    
    Field yang diizinkan edit (sesuai kebijakan):
    - Data identitas: NIK, tempat/tgl lahir, jenis kelamin
    - Status: agama, kewarganegaraan, status nikah, kebutuhan khusus
    - Alamat: alamat lengkap, RT/RW, kelurahan, kode pos
      (provinsi/kab/kec tidak diedit di sini karena pakai dropdown master)
    
    Field yang TIDAK boleh diedit:
    - jalur, gelombang, prodi (keputusan akademik)
    - status pendaftaran (sudah ada workflow ubah_status)
    - data ortu (akan di-handle form terpisah)
    - data pendidikan (akan di-handle form terpisah)
    - foto, ukuran_baju (urusan maba)
    """
    
    
    
    # Field nama (tersimpan di model User, bukan ProfilPendaftar)
    first_name = forms.CharField(
        required=True,
        label='Nama Depan',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sesuai ijazah (huruf kapital di awal kata)',
        }),
        help_text='Tersimpan di akun User. Pastikan sesuai ijazah/akta.',
    )
    last_name = forms.CharField(
        required=False,
        label='Nama Belakang',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kosongkan jika hanya satu kata',
        }),
        help_text='Boleh dikosongkan jika nama hanya terdiri dari satu kata.',
    )
    
    # Field WAJIB ada (operator harus isi alasan kenapa edit)
    alasan_edit = forms.CharField(
        required=True,
        label='Alasan Edit',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Wajib diisi. Contoh: "Koreksi tipo nama sesuai ijazah" atau "Maba datang ke kampus untuk update data"',
        }),
        help_text='Akan tercatat di audit log bersama nama operator dan timestamp.',
    )
    
    class Meta:
        model = ProfilPendaftar
        fields = [
            # Data identitas
            'nik',
            'tempat_lahir',
            'tgl_lahir',
            'jenis_kelamin',
            'kewarganegaraan',
            'status_nikah',
            'kebutuhan_khusus',
            # Alamat
            'alamat_lengkap',
            'kelurahan',
            'kode_pos',
        ]
        widgets = {
            'nik': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '16 digit NIK sesuai KTP',
                'maxlength': '16',
            }),
            'tempat_lahir': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sesuai akta kelahiran',
            }),
            'tgl_lahir': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'jenis_kelamin': forms.Select(
                choices=JENIS_KELAMIN_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'kewarganegaraan': forms.Select(
                choices=KEWARGANEGARAAN_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'status_nikah': forms.Select(
                choices=STATUS_NIKAH_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'kebutuhan_khusus': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: tuna rungu, autis (kosongkan jika tidak ada)',
            }),
            'alamat_lengkap': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Jl. ..., RT/RW, dll',
            }),
            'kelurahan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama kelurahan/desa',
            }),
            'kode_pos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '5 digit kode pos',
                'maxlength': '5',
            }),
        }
        labels = {
            'nik': 'Nomor Induk Kependudukan (NIK)',
            'tempat_lahir': 'Tempat Lahir',
            'tgl_lahir': 'Tanggal Lahir',
            'jenis_kelamin': 'Jenis Kelamin',
            'kewarganegaraan': 'Kewarganegaraan',
            'status_nikah': 'Status Pernikahan',
            'kebutuhan_khusus': 'Kebutuhan Khusus',
            'alamat_lengkap': 'Alamat Lengkap',
            'kelurahan': 'Kelurahan / Desa',
            'kode_pos': 'Kode Pos',
        }
    def __init__(self, *args, **kwargs):
        """Populate first_name & last_name dari User yang terkait dengan Pendaftaran."""
        super().__init__(*args, **kwargs)
        # ProfilPendaftar -> pendaftaran (FK) -> user (OneToOne)
        if self.instance and self.instance.pk:
            try:
                user = self.instance.pendaftaran.user
                self.fields['first_name'].initial = user.first_name
                self.fields['last_name'].initial = user.last_name
            except AttributeError:
                # Fallback aman jika instance belum punya pendaftaran.user
                pass

    def clean_first_name(self):
        """Auto-uppercase nama depan untuk konsistensi data."""
        first_name = self.cleaned_data.get('first_name', '')
        return first_name.upper() if first_name else first_name
    
    def clean_last_name(self):
        """Auto-uppercase nama belakang untuk konsistensi data."""
        last_name = self.cleaned_data.get('last_name', '')
        return last_name.upper() if last_name else last_name


class OperatorEditDataOrtuForm(forms.ModelForm):
    """
    Form untuk operator/admin PMB edit data orang tua pendaftar.
    
    Reuse struktur dari ProfilOrtuForm tapi tanpa field maba-only.
    """
    
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
    
    PENGHASILAN_CHOICES = [
        ('', '-- Pilih Range Penghasilan --'),
        ('< 1jt',  'Di bawah Rp 1.000.000'),
        ('1-3jt',  'Rp 1.000.000 – Rp 3.000.000'),
        ('3-5jt',  'Rp 3.000.000 – Rp 5.000.000'),
        ('5-10jt', 'Rp 5.000.000 – Rp 10.000.000'),
        ('> 10jt', 'Di atas Rp 10.000.000'),
    ]
    
    pekerjaan_ayah = forms.ChoiceField(
        choices=PEKERJAAN_CHOICES,
        required=False,
        label='Pekerjaan Ayah',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    pekerjaan_ibu = forms.ChoiceField(
        choices=PEKERJAAN_CHOICES,
        required=False,
        label='Pekerjaan Ibu',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
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
    penghasilan_ayah = forms.ChoiceField(
        choices=PENGHASILAN_CHOICES,
        required=False,
        label='Penghasilan Ayah',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    penghasilan_ibu = forms.ChoiceField(
        choices=PENGHASILAN_CHOICES,
        required=False,
        label='Penghasilan Ibu',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Field WAJIB
    alasan_edit = forms.CharField(
        required=True,
        label='Alasan Edit',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Wajib diisi. Contoh: "Koreksi data ortu sesuai KK"',
        }),
        help_text='Akan tercatat di audit log.',
    )
    
    class Meta:
        model = ProfilPendaftar
        fields = [
            'nama_ayah', 'pekerjaan_ayah', 'pendidikan_ayah', 'penghasilan_ayah', 'no_hp_ayah',
            'nama_ibu',  'pekerjaan_ibu',  'pendidikan_ibu',  'penghasilan_ibu',  'no_hp_ibu',
            'nama_wali', 'no_hp_ortu', 'alamat_ortu',
        ]
        widgets = {
            'nama_ayah': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap ayah kandung'}),
            'no_hp_ayah': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No HP aktif ayah'}),
            'nama_ibu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap ibu kandung'}),
            'no_hp_ibu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No HP aktif ibu'}),
            'nama_wali': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama wali (jika bukan ortu)'}),
            'no_hp_ortu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No HP ortu/wali yang dihubungi'}),
            'alamat_ortu': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Alamat ortu/wali'}),
        }

