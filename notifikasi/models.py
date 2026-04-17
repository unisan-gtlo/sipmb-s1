from django.db import models
from accounts.models import User
from pendaftaran.models import Pendaftaran


class TemplateNotifikasi(models.Model):
    JENIS_CHOICES = [
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Email & WhatsApp'),
    ]
    TRIGGER_CHOICES = [
        ('registrasi',      'Setelah Registrasi'),
        ('aktivasi',        'Setelah Aktivasi Email'),
        ('profil_lengkap',  'Profil Lengkap'),
        ('dokumen_upload',  'Dokumen Diupload'),
        ('dokumen_acc',     'Dokumen Diverifikasi'),
        ('dokumen_tolak',   'Dokumen Ditolak'),
        ('terjadwal',       'Terjadwal Seleksi'),
        ('lulus_seleksi',   'Lulus Seleksi'),
        ('tidak_lulus',     'Tidak Lulus Seleksi'),
        ('daftar_ulang',    'Pengingat Daftar Ulang'),
        ('pembayaran',      'Konfirmasi Pembayaran'),
        ('manual',          'Kirim Manual'),
    ]

    nama        = models.CharField(max_length=200)
    trigger     = models.CharField(max_length=20, choices=TRIGGER_CHOICES, unique=True)
    jenis       = models.CharField(max_length=10, choices=JENIS_CHOICES, default='both')
    subjek_email= models.CharField(max_length=200, blank=True)
    isi_email   = models.TextField(blank=True,
                    help_text='Gunakan {{nama}}, {{no_pendaftaran}}, {{prodi}}, {{jalur}}, {{status}}')
    isi_wa      = models.TextField(blank=True,
                    help_text='Pesan WhatsApp. Gunakan {{nama}}, {{no_pendaftaran}}, dst')
    aktif       = models.BooleanField(default=True)
    tgl_update  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'pmb\".\"template_notifikasi'
        verbose_name = 'Template Notifikasi'
        verbose_name_plural = 'Template Notifikasi'

    def __str__(self):
        return f'{self.nama} ({self.get_trigger_display()})'


class LogNotifikasi(models.Model):
    STATUS_CHOICES = [
        ('terkirim', 'Terkirim'),
        ('gagal',    'Gagal'),
        ('pending',  'Pending'),
    ]

    pendaftaran = models.ForeignKey(
        Pendaftaran, on_delete=models.CASCADE,
        related_name='notifikasi', null=True, blank=True
    )
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    template    = models.ForeignKey(
        TemplateNotifikasi, on_delete=models.SET_NULL, null=True
    )
    jenis       = models.CharField(max_length=10)
    tujuan      = models.CharField(max_length=200, help_text='Email atau nomor WA')
    subjek      = models.CharField(max_length=200, blank=True)
    isi         = models.TextField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_msg   = models.TextField(blank=True)
    tgl_kirim   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'pmb\".\"log_notifikasi'
        ordering     = ['-tgl_kirim']
        verbose_name = 'Log Notifikasi'
        verbose_name_plural = 'Log Notifikasi'

    def __str__(self):
        return f'{self.jenis} → {self.tujuan} ({self.status})'