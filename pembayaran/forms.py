# pembayaran/forms.py
from django import forms
from django.utils import timezone

from .models import KonfirmasiPembayaran, RekeningTujuan


class UploadBuktiForm(forms.ModelForm):
    class Meta:
        model = KonfirmasiPembayaran
        fields = [
            'metode_bayar',
            'rekening_tujuan',
            'bank_asal',
            'atas_nama_pengirim',
            'jumlah_bayar',
            'tgl_bayar',
            'no_transaksi',
            'bukti_bayar',
            'catatan_pengirim',
        ]
        widgets = {
            'metode_bayar': forms.Select(attrs={'class': 'form-select'}),
            'rekening_tujuan': forms.Select(attrs={'class': 'form-select'}),
            'bank_asal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: BCA, SeaBank, Dana, OVO',
            }),
            'atas_nama_pengirim': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama sesuai rekening pengirim',
            }),
            'jumlah_bayar': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 1,
            }),
            'tgl_bayar': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'no_transaksi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opsional — nomor referensi transfer',
            }),
            'bukti_bayar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'catatan_pengirim': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Catatan tambahan (opsional)',
            }),
        }
        labels = {
            'bank_asal': 'Bank/E-wallet Pengirim',
            'atas_nama_pengirim': 'Atas Nama Pengirim',
            'jumlah_bayar': 'Jumlah Transfer (Rp)',
            'tgl_bayar': 'Tanggal Transfer',
            'no_transaksi': 'No. Referensi (opsional)',
            'bukti_bayar': 'Foto/Scan Bukti Transfer',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rekening_tujuan'].queryset = (
            RekeningTujuan.objects.filter(aktif=True)
        )
        self.fields['rekening_tujuan'].empty_label = "-- Pilih rekening tujuan --"

    def clean_bukti_bayar(self):
        file = self.cleaned_data.get('bukti_bayar')
        if file:
            max_size = 5 * 1024 * 1024  # 5 MB
            if file.size > max_size:
                raise forms.ValidationError(
                    f"Ukuran file maksimal 5 MB. File Anda: "
                    f"{file.size / 1024 / 1024:.2f} MB."
                )
        return file

    def clean_tgl_bayar(self):
        tgl = self.cleaned_data.get('tgl_bayar')
        if tgl and tgl > timezone.now().date():
            raise forms.ValidationError(
                "Tanggal transfer tidak boleh di masa depan."
            )
        return tgl