from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User
from master.models import JalurPenerimaan, GelombangPenerimaan, ProdiPMB


class RegistrasiAwalForm(forms.Form):
    # Data minimal untuk mendapatkan akun
    nama_lengkap = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama lengkap sesuai ijazah',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email aktif untuk aktivasi',
        })
    )
    no_hp = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nomor HP / WhatsApp aktif',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password minimal 8 karakter',
        })
    )
    konfirmasi_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ulangi password',
        })
    )
    jalur = forms.ModelChoiceField(
        queryset=JalurPenerimaan.objects.filter(status='aktif').order_by('urutan'),
        empty_label='-- Pilih Jalur Penerimaan --',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_jalur'})
    )
    gelombang = forms.ModelChoiceField(
        queryset=GelombangPenerimaan.objects.filter(status='buka'),
        empty_label='-- Pilih Gelombang --',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_gelombang'})
    )
    prodi_pilihan_1 = forms.ModelChoiceField(
        queryset=ProdiPMB.objects.filter(status='aktif'),
        empty_label='-- Pilih Program Studi Pilihan 1 --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prodi_pilihan_2 = forms.ModelChoiceField(
        queryset=ProdiPMB.objects.filter(status='aktif'),
        empty_label='-- Pilih Program Studi Pilihan 2 (Opsional) --',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    kode_referral = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kode referral (jika ada)',
        })
    )
    kode_voucher = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kode voucher diskon (jika ada)',
        })
    )
    setuju_syarat = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Anda harus menyetujui syarat dan ketentuan.'}
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email ini sudah terdaftar. Gunakan email lain atau login.')
        return email.lower()

    def clean_no_hp(self):
        no_hp = self.cleaned_data.get('no_hp', '').strip()
        # Normalisasi: 08xx → 628xx
        if no_hp.startswith('0'):
            no_hp = '62' + no_hp[1:]
        return no_hp

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        password         = cleaned.get('password')
        konfirmasi       = cleaned.get('konfirmasi_password')
        prodi_1          = cleaned.get('prodi_pilihan_1')
        prodi_2          = cleaned.get('prodi_pilihan_2')

        if password and konfirmasi and password != konfirmasi:
            self.add_error('konfirmasi_password', 'Password tidak cocok.')

        if prodi_1 and prodi_2 and prodi_1 == prodi_2:
            self.add_error('prodi_pilihan_2', 'Pilihan 2 tidak boleh sama dengan pilihan 1.')

        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email pendaftaran',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password',
        })
    )
    captcha_confirm = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'Harap centang "Saya bukan robot" untuk melanjutkan.',
        },
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_captcha_confirm',
        })
    )