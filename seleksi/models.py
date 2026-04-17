from django.db import models
from accounts.models import User
from pendaftaran.models import Pendaftaran
from master.models import JalurPenerimaan, GelombangPenerimaan, ProdiPMB


class JadwalSeleksi(models.Model):
    JENIS_CHOICES = [
        ('tes_tulis',    'Tes Tulis'),
        ('wawancara',    'Wawancara'),
        ('tes_praktik',  'Tes Praktik'),
        ('portofolio',   'Review Portofolio'),
        ('administrasi', 'Seleksi Administrasi'),
    ]
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('publish',   'Dipublikasi'),
        ('selesai',   'Selesai'),
        ('batal',     'Dibatalkan'),
    ]

    jalur           = models.ForeignKey(JalurPenerimaan, on_delete=models.CASCADE)
    gelombang       = models.ForeignKey(GelombangPenerimaan, on_delete=models.CASCADE)
    jenis_seleksi   = models.CharField(max_length=15, choices=JENIS_CHOICES)
    nama_seleksi    = models.CharField(max_length=200)
    tgl_seleksi     = models.DateField()
    jam_mulai       = models.TimeField()
    jam_selesai     = models.TimeField()
    lokasi          = models.CharField(max_length=200, blank=True)
    link_online     = models.URLField(blank=True, help_text='Link Zoom/Meet jika online')
    keterangan      = models.TextField(blank=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    dibuat_oleh     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tgl_dibuat      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'pmb\".\"jadwal_seleksi'
        ordering     = ['tgl_seleksi', 'jam_mulai']
        verbose_name = 'Jadwal Seleksi'
        verbose_name_plural = 'Jadwal Seleksi'

    def __str__(self):
        return f'{self.nama_seleksi} — {self.tgl_seleksi}'


class PesertaSeleksi(models.Model):
    STATUS_CHOICES = [
        ('terdaftar', 'Terdaftar'),
        ('hadir',     'Hadir'),
        ('tidak_hadir','Tidak Hadir'),
        ('izin',      'Izin'),
    ]

    jadwal          = models.ForeignKey(JadwalSeleksi, on_delete=models.CASCADE, related_name='peserta')
    pendaftaran     = models.ForeignKey(Pendaftaran, on_delete=models.CASCADE, related_name='seleksi')
    no_ujian        = models.CharField(max_length=20, blank=True)
    status_kehadiran= models.CharField(max_length=15, choices=STATUS_CHOICES, default='terdaftar')
    nilai           = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    catatan_penilai = models.TextField(blank=True)
    dinilai_oleh    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='penilaian'
    )
    tgl_penilaian   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table     = 'pmb\".\"peserta_seleksi'
        unique_together = ['jadwal', 'pendaftaran']
        verbose_name = 'Peserta Seleksi'
        verbose_name_plural = 'Peserta Seleksi'

    def __str__(self):
        return f'{self.pendaftaran.no_pendaftaran} — {self.jadwal.nama_seleksi}'


class HasilPenerimaan(models.Model):
    STATUS_CHOICES = [
        ('lulus',          'Lulus'),
        ('tidak_lulus',    'Tidak Lulus'),
        ('cadangan',       'Cadangan'),
        ('lulus_bersyarat','Lulus Bersyarat'),
    ]

    pendaftaran     = models.OneToOneField(
        Pendaftaran, on_delete=models.CASCADE, related_name='hasil'
    )
    prodi_diterima  = models.ForeignKey(
        ProdiPMB, on_delete=models.SET_NULL, null=True,
        help_text='Prodi yang diterima (bisa berbeda dari pilihan 1)'
    )
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES)
    nilai_akhir     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    peringkat       = models.IntegerField(null=True, blank=True)
    catatan         = models.TextField(blank=True)
    tgl_pengumuman  = models.DateField(null=True, blank=True)
    sudah_daftar_ulang = models.BooleanField(default=False)
    tgl_daftar_ulang= models.DateTimeField(null=True, blank=True)
    diinput_oleh    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    tgl_diinput     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'pmb\".\"hasil_penerimaan'
        ordering     = ['peringkat', 'nilai_akhir']
        verbose_name = 'Hasil Penerimaan'
        verbose_name_plural = 'Hasil Penerimaan'

    def __str__(self):
        return f'{self.pendaftaran.no_pendaftaran} — {self.status}'


class KartuPeserta(models.Model):
    """Kartu ujian/peserta seleksi"""
    pendaftaran     = models.OneToOneField(
        Pendaftaran, on_delete=models.CASCADE, related_name='kartu'
    )
    no_kartu        = models.CharField(max_length=30, unique=True)
    tgl_cetak       = models.DateTimeField(auto_now_add=True)
    sudah_cetak     = models.BooleanField(default=False)

    class Meta:
        db_table     = 'pmb\".\"kartu_peserta'
        verbose_name = 'Kartu Peserta'

    def __str__(self):
        return f'Kartu {self.no_kartu}'