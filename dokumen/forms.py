from django import forms
from .models import DokumenPendaftar


class UploadDokumenForm(forms.ModelForm):
    class Meta:
        model  = DokumenPendaftar
        fields = ['file', 'link_drive']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'link_drive': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://drive.google.com/... (opsional jika tidak upload file)',
            }),
        }

    def clean(self):
        cleaned    = super().clean()
        file       = cleaned.get('file')
        link_drive = cleaned.get('link_drive')
        if not file and not link_drive:
            raise forms.ValidationError('Upload file atau isi link Google Drive.')
        return cleaned