# pembayaran/models.py
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_kode_bayar():
    """Generate kode unik: INV-2026-XXXXXX"""
    year = timezone.now().year
    random_part = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )
    return f"INV-{year}-{random_part}"


class RekeningTujuan(models.Model):
    """Rekening bank resmi kampus untuk transfer pembayaran PMB."""
    nama_bank = models.CharField(max_length=50, help_text="Contoh: BRI, BNI, Mandiri, BSI")
    no_rekening = models.CharField(max_length=30)
    atas_nama = models.CharField(max_length=100, help_text="Nama pemilik rekening (biasanya 'Universitas Ichsan Gorontalo')")
    cabang = models.CharField(max_length=100, blank=True)
    logo_bank = models.ImageField(upload_to='rekening/', blank=True, null=True, help_text="Logo bank untuk tampilan (opsional)")
    urutan = models.PositiveIntegerField(default=0, help_text="Urutan tampil — semakin kecil semakin atas")
    aktif = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['urutan', 'nama_bank']
        verbose_name = "Rekening Tujuan"
        verbose_name_plural = "Rekening Tujuan"

    def __str__(self):
        return f"{self.nama_bank} - {self.no_rekening} a.n. {self.atas_nama}"


class Tagihan(models.Model):
    JENIS_CHOICES = [
        ('biaya_pendaftaran', 'Biaya Pendaftaran'),
        ('daftar_ulang', 'Daftar Ulang'),
        ('ukt', 'UKT / SPP'),
    ]
    STATUS_CHOICES = [
        ('belum_bayar', 'Belum Bayar'),
        ('menunggu_konfirmasi', 'Menunggu Konfirmasi'),
        ('lunas', 'Lunas'),
        ('expired', 'Expired'),
        ('dibatalkan', 'Dibatalkan'),
    ]

    pendaftaran = models.ForeignKey(
        'pendaftaran.Pendaftaran',
        on_delete=models.CASCADE,
        related_name='tagihan',
    )
    jenis = models.CharField(max_length=30, choices=JENIS_CHOICES, default='biaya_pendaftaran')
    jumlah = models.DecimalField(max_digits=12, decimal_places=0)
    tgl_tagihan = models.DateField(default=timezone.now)
    tgl_jatuh_tempo = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='belum_bayar', db_index=True)
    kode_bayar = models.CharField(max_length=30, unique=True, default=generate_kode_bayar, editable=False, db_index=True)
    catatan = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tagihan"
        verbose_name_plural = "Tagihan"
        indexes = [
            models.Index(fields=['pendaftaran', 'status']),
        ]

    def __str__(self):
        return f"{self.kode_bayar} — {self.pendaftaran.no_pendaftaran}"

    def save(self, *args, **kwargs):
        # Default jatuh tempo: 7 hari dari tanggal tagihan
        if not self.tgl_jatuh_tempo:
            base = self.tgl_tagihan or timezone.now().date()
            self.tgl_jatuh_tempo = base + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def sudah_lunas(self):
        return self.status == 'lunas'

    @property
    def is_expired(self):
        if self.status == 'lunas':
            return False
        return self.tgl_jatuh_tempo and self.tgl_jatuh_tempo < timezone.now().date()

    @property
    def is_gratis(self):
        return self.jumlah == 0


class KonfirmasiPembayaran(models.Model):
    METODE_CHOICES = [
        ('transfer_bank', 'Transfer Bank'),
        ('tunai', 'Tunai (Kasir PMB)'),
        ('qris', 'QRIS'),
    ]
    STATUS_CHOICES = [
        ('menunggu', 'Menunggu Verifikasi'),
        ('dikonfirmasi', 'Dikonfirmasi'),
        ('ditolak', 'Ditolak'),
    ]

    tagihan = models.ForeignKey(
        Tagihan,
        on_delete=models.CASCADE,
        related_name='konfirmasi',
    )
    metode_bayar = models.CharField(max_length=20, choices=METODE_CHOICES, default='transfer_bank')
    rekening_tujuan = models.ForeignKey(
        RekeningTujuan,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Rekening tujuan yang dipilih maba saat transfer",
    )
    bank_asal = models.CharField(max_length=50, blank=True, help_text="Bank pengirim (contoh: BCA, SeaBank)")
    atas_nama_pengirim = models.CharField(max_length=100, blank=True)
    jumlah_bayar = models.DecimalField(max_digits=12, decimal_places=0)
    tgl_bayar = models.DateField(help_text="Tanggal transfer dilakukan")
    bukti_bayar = models.ImageField(upload_to='bukti_bayar/%Y/%m/')
    no_transaksi = models.CharField(max_length=100, blank=True, help_text="Nomor referensi bank (opsional)")

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='menunggu', db_index=True)
    catatan_pengirim = models.TextField(blank=True, help_text="Catatan dari maba")
    catatan_admin = models.TextField(blank=True, help_text="Catatan admin saat verifikasi/tolak")

    dikonfirmasi_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pembayaran_diverifikasi',
    )
    tgl_konfirmasi = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Konfirmasi Pembayaran"
        verbose_name_plural = "Konfirmasi Pembayaran"

    def __str__(self):
        return f"{self.tagihan.kode_bayar} — {self.get_status_display()}"