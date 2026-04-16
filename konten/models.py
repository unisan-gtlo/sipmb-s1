from django.db import models


class BrosurFakultas(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    # Referensi ke SIMDA via kode
    kode_fakultas = models.CharField(max_length=10)
    nama_fakultas = models.CharField(max_length=200)
    judul         = models.CharField(max_length=200)
    gambar        = models.ImageField(upload_to='brosur/', blank=True, null=True)
    file_pdf      = models.FileField(upload_to='brosur/pdf/', blank=True, null=True)
    deskripsi     = models.TextField(blank=True)
    link_video    = models.URLField(blank=True, help_text='Link video YouTube profil fakultas')
    urutan        = models.IntegerField(default=0)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    tgl_upload    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'pmb\".\"brosur_fakultas'
        ordering    = ['urutan', 'nama_fakultas']
        verbose_name = 'Brosur Fakultas'
        verbose_name_plural = 'Brosur Fakultas'

    def __str__(self):
        return f'{self.nama_fakultas} — {self.judul}'


class GaleriKampus(models.Model):
    KATEGORI_CHOICES = [
        ('gedung',    'Gedung & Fasilitas'),
        ('kegiatan',  'Kegiatan Mahasiswa'),
        ('fasilitas', 'Fasilitas Kampus'),
        ('prestasi',  'Prestasi'),
        ('wisuda',    'Wisuda'),
    ]
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    judul      = models.CharField(max_length=200)
    gambar     = models.ImageField(upload_to='galeri/', blank=True, null=True)
    link_video = models.URLField(blank=True, help_text='Link video YouTube (opsional)')
    kategori   = models.CharField(max_length=15, choices=KATEGORI_CHOICES, default='kegiatan')
    urutan     = models.IntegerField(default=0)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    class Meta:
        db_table    = 'pmb\".\"galeri_kampus'
        ordering    = ['urutan', 'judul']
        verbose_name = 'Galeri Kampus'
        verbose_name_plural = 'Galeri Kampus'

    def __str__(self):
        return self.judul


class Pengumuman(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    judul         = models.CharField(max_length=300)
    isi           = models.TextField()
    file_lampiran = models.FileField(upload_to='pengumuman/', blank=True, null=True)
    tgl_tayang    = models.DateField()
    tgl_selesai   = models.DateField(null=True, blank=True)
    penting       = models.BooleanField(default=False)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    tgl_dibuat    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'pmb\".\"pengumuman'
        ordering    = ['-penting', '-tgl_tayang']
        verbose_name = 'Pengumuman'
        verbose_name_plural = 'Pengumuman'

    def __str__(self):
        return self.judul


class FAQ(models.Model):
    KATEGORI_CHOICES = [
        ('umum',      'Umum'),
        ('biaya',     'Biaya & Pembayaran'),
        ('jadwal',    'Jadwal & Gelombang'),
        ('dokumen',   'Dokumen Persyaratan'),
        ('seleksi',   'Seleksi & Tes'),
        ('daftar_ulang', 'Daftar Ulang'),
        ('beasiswa',  'Beasiswa'),
        ('prodi',     'Program Studi'),
    ]
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    pertanyaan = models.CharField(max_length=500)
    jawaban    = models.TextField()
    kategori   = models.CharField(max_length=15, choices=KATEGORI_CHOICES, default='umum')
    urutan     = models.IntegerField(default=0)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    class Meta:
        db_table    = 'pmb\".\"faq'
        ordering    = ['kategori', 'urutan']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'

    def __str__(self):
        return self.pertanyaan


class Testimoni(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    nama           = models.CharField(max_length=200)
    prodi          = models.CharField(max_length=200)
    angkatan       = models.CharField(max_length=10)
    foto           = models.ImageField(upload_to='testimoni/', blank=True, null=True)
    isi_testimoni  = models.TextField()
    urutan         = models.IntegerField(default=0)
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    class Meta:
        db_table    = 'pmb\".\"testimoni'
        ordering    = ['urutan']
        verbose_name = 'Testimoni'
        verbose_name_plural = 'Testimoni'

    def __str__(self):
        return f'{self.nama} — {self.prodi} {self.angkatan}'


class MitraKerjasama(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    nama_mitra  = models.CharField(max_length=200)
    logo        = models.ImageField(upload_to='mitra/', blank=True, null=True)
    website     = models.URLField(blank=True)
    keterangan  = models.TextField(blank=True)
    urutan      = models.IntegerField(default=0)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    class Meta:
        db_table    = 'pmb\".\"mitra_kerjasama'
        ordering    = ['urutan', 'nama_mitra']
        verbose_name = 'Mitra Kerjasama'
        verbose_name_plural = 'Mitra Kerjasama'

    def __str__(self):
        return self.nama_mitra


class MediaSosial(models.Model):
    PLATFORM_CHOICES = [
        ('facebook',  'Facebook'),
        ('instagram', 'Instagram'),
        ('youtube',   'YouTube'),
        ('tiktok',    'TikTok'),
        ('twitter',   'Twitter / X'),
        ('whatsapp',  'WhatsApp'),
        ('telegram',  'Telegram'),
    ]
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    platform   = models.CharField(max_length=15, choices=PLATFORM_CHOICES)
    nama_akun  = models.CharField(max_length=100)
    url        = models.URLField()
    urutan     = models.IntegerField(default=0)
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    class Meta:
        db_table    = 'pmb\".\"media_sosial'
        ordering    = ['urutan']
        verbose_name = 'Media Sosial'
        verbose_name_plural = 'Media Sosial'

    def __str__(self):
        return f'{self.get_platform_display()} — {self.nama_akun}'


class DokumenDownload(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    judul    = models.CharField(max_length=200)
    file     = models.FileField(upload_to='download/')
    ukuran   = models.CharField(max_length=20, blank=True)
    urutan   = models.IntegerField(default=0)
    status   = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    tgl_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'pmb\".\"dokumen_download'
        ordering    = ['urutan']
        verbose_name = 'Dokumen Download'
        verbose_name_plural = 'Dokumen Download'

    def __str__(self):
        return self.judul