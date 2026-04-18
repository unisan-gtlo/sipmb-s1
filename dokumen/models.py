from django.db import models
from pendaftaran.models import Pendaftaran
from master.models import PersyaratanJalur
from utils.validators import validate_document_or_image

class DokumenPendaftar(models.Model):
    STATUS_CHOICES = [
        ('belum',        'Belum Diupload'),
        ('menunggu',     'Menunggu Verifikasi'),
        ('terverifikasi','Terverifikasi'),
        ('ditolak',      'Ditolak'),
    ]

    pendaftaran       = models.ForeignKey(Pendaftaran, on_delete=models.CASCADE, related_name='dokumen')
    persyaratan       = models.ForeignKey(PersyaratanJalur, on_delete=models.PROTECT)
    nama_file         = models.CharField(max_length=200, blank=True)
    file              = models.FileField(upload_to='dokumen_pendaftar/', blank=True, null=True)
    link_drive        = models.URLField(blank=True, help_text='Alternatif link Google Drive')
    status_verifikasi = models.CharField(max_length=15, choices=STATUS_CHOICES, default='menunggu')
    catatan_verifikasi= models.TextField(blank=True)
    tgl_upload        = models.DateTimeField(auto_now_add=True)
    tgl_verifikasi    = models.DateTimeField(null=True, blank=True)
    validators=[validate_document_or_image],
    diverifikasi_oleh = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='dokumen_diverifikasi'
    )

    class Meta:
        db_table    = 'pmb\".\"dokumen_pendaftar'
        ordering    = ['persyaratan__urutan']
        verbose_name = 'Dokumen Pendaftar'
        verbose_name_plural = 'Dokumen Pendaftar'
        unique_together = ['pendaftaran', 'persyaratan']

    def __str__(self):
        return f'{self.pendaftaran.no_pendaftaran} — {self.persyaratan.nama_dokumen}'

    @property
    def sudah_upload(self):
        return bool(self.file or self.link_drive)

    @property
    def nama_dokumen(self):
        return self.persyaratan.nama_dokumen

    @property
    def wajib(self):
        return self.persyaratan.wajib