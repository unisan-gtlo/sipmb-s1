from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class JalurPenerimaan(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    kode_jalur   = models.CharField(max_length=10, unique=True)
    nama_jalur   = models.CharField(max_length=100)
    deskripsi    = models.TextField(blank=True)
    syarat_umum  = models.TextField(blank=True)
    ada_tes      = models.BooleanField(default=False)
    ada_wawancara= models.BooleanField(default=False)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    urutan       = models.IntegerField(default=0)
    # === TAMBAHAN: Tampilan di web publik ===
    icon = models.CharField(
        max_length=50,
        default='ti-school',
        help_text="Nama icon Tabler (contoh: ti-school, ti-pencil, ti-star, ti-trophy)",
        verbose_name="Icon"
    )
    warna = models.CharField(
        max_length=20,
        default='purple',
        choices=[
            ('purple', 'Ungu'),
            ('blue', 'Biru'),
            ('green', 'Hijau'),
            ('red', 'Merah'),
            ('orange', 'Oranye'),
            ('teal', 'Teal'),
            ('pink', 'Pink'),
            ('indigo', 'Indigo'),
        ],
        help_text="Warna gradient icon jalur",
        verbose_name="Warna Tampilan"
    )
    class Meta:
        db_table    = 'pmb\".\"jalur_penerimaan'
        ordering    = ['urutan', 'nama_jalur']
        verbose_name = 'Jalur Penerimaan'
        verbose_name_plural = 'Jalur Penerimaan'

    def __str__(self):
        return f'{self.kode_jalur} — {self.nama_jalur}'


class GelombangPenerimaan(models.Model):
    STATUS_CHOICES = [
        ('belum_buka', 'Belum Dibuka'),
        ('buka',       'Dibuka'),
        ('ditutup',    'Ditutup'),
        ('selesai',    'Selesai'),
    ]
    JENIS_BIAYA_CHOICES = [
        ('gratis',   'Gratis'),
        ('potongan', 'Potongan'),
        ('full',     'Full / Normal'),
    ]

    nama_gelombang    = models.CharField(max_length=50)
    tahun_akademik    = models.CharField(max_length=10)
    jalur             = models.ForeignKey(JalurPenerimaan, on_delete=models.PROTECT, related_name='gelombang')
    tgl_buka          = models.DateField()
    tgl_tutup         = models.DateField()
    tgl_seleksi       = models.DateField(null=True, blank=True)
    tgl_pengumuman    = models.DateField(null=True, blank=True)
    tgl_daftar_ulang  = models.DateField(null=True, blank=True)
    jenis_biaya       = models.CharField(max_length=10, choices=JENIS_BIAYA_CHOICES, default='full')
    biaya_penuh       = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    persen_potongan   = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    nominal_potongan  = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    biaya_akhir       = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    keterangan_biaya  = models.TextField(blank=True)
    berlaku_sampai    = models.DateField(null=True, blank=True)
    kuota_total       = models.IntegerField(default=0)
    status            = models.CharField(max_length=15, choices=STATUS_CHOICES, default='belum_buka')
    keterangan        = models.TextField(blank=True)
   

    class Meta:
        db_table    = 'pmb\".\"gelombang_penerimaan'
        ordering    = ['tahun_akademik', 'jalur', 'nama_gelombang']
        verbose_name = 'Gelombang Penerimaan'
        verbose_name_plural = 'Gelombang Penerimaan'

    def __str__(self):
        return f'{self.nama_gelombang} — {self.jalur.nama_jalur} ({self.tahun_akademik})'

    def save(self, *args, **kwargs):
        # Auto hitung biaya akhir
        if self.jenis_biaya == 'gratis':
            self.biaya_akhir = 0
        elif self.jenis_biaya == 'potongan':
            if self.persen_potongan > 0:
                self.nominal_potongan = self.biaya_penuh * self.persen_potongan / 100
            self.biaya_akhir = self.biaya_penuh - self.nominal_potongan
        else:
            self.biaya_akhir = self.biaya_penuh
        super().save(*args, **kwargs)


class ProdiPMB(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    # Referensi ke SIMDA via kode (bukan FK langsung)
    kode_prodi   = models.CharField(max_length=10)
    nama_prodi   = models.CharField(max_length=200)
    kode_fakultas= models.CharField(max_length=10)
    nama_fakultas= models.CharField(max_length=200)
    gelombang    = models.ForeignKey(GelombangPenerimaan, on_delete=models.PROTECT, related_name='prodi_pmb')
    kuota        = models.IntegerField(default=0)
    daya_tampung = models.IntegerField(default=0)
    biaya_kuliah = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    biaya_spp    = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    class Meta:
        db_table    = 'pmb\".\"prodi_pmb'
        ordering    = ['kode_fakultas', 'nama_prodi']
        verbose_name = 'Prodi PMB'
        verbose_name_plural = 'Prodi PMB'
        unique_together = ['kode_prodi', 'gelombang']

    def __str__(self):
        return f'{self.nama_prodi} — {self.gelombang}'


class PersyaratanJalur(models.Model):
    FORMAT_CHOICES = [
        ('PDF',      'PDF'),
        ('JPG',      'JPG / JPEG'),
        ('PNG',      'PNG'),
        ('PDF_IMG',  'PDF / JPG / PNG'),
    ]

    jalur         = models.ForeignKey(JalurPenerimaan, on_delete=models.CASCADE, related_name='persyaratan')
    nama_dokumen  = models.CharField(max_length=200)
    keterangan    = models.TextField(blank=True)
    wajib         = models.BooleanField(default=True)
    format_file   = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='PDF_IMG')
    ukuran_max    = models.IntegerField(default=5, help_text='Ukuran maksimal dalam MB')
    urutan        = models.IntegerField(default=0)

    class Meta:
        db_table    = 'pmb\".\"persyaratan_jalur'
        ordering    = ['jalur', 'urutan']
        verbose_name = 'Persyaratan Jalur'
        verbose_name_plural = 'Persyaratan Jalur'

    def __str__(self):
        return f'{self.jalur.kode_jalur} — {self.nama_dokumen}'


class PengaturanSistem(models.Model):
    STATUS_CHOICES = [
        ('buka',  'Buka'),
        ('tutup', 'Tutup'),
    ]

    # Info kampus
    tahun_akademik_aktif = models.CharField(max_length=10, default='2025/2026')
    nama_rektor          = models.CharField(max_length=200, blank=True)
    nama_wakil_rektor    = models.CharField(max_length=200, blank=True)
    no_telepon_pmb       = models.CharField(max_length=20, blank=True)
    email_pmb            = models.EmailField(blank=True)
    whatsapp_pmb         = models.CharField(max_length=20, blank=True)
    alamat_kampus        = models.TextField(blank=True)
    logo                 = models.ImageField(upload_to='pengaturan/', blank=True, null=True)
    banner_utama         = models.ImageField(upload_to='pengaturan/', blank=True, null=True)
    teks_sambutan        = models.TextField(blank=True)
    status_pendaftaran   = models.CharField(max_length=5, choices=STATUS_CHOICES, default='buka')

    # WhatsApp Group
    link_wa_group        = models.URLField(blank=True)
    nama_wa_group        = models.CharField(max_length=100, blank=True)
    deskripsi_wa_group   = models.TextField(blank=True)
    tampilkan_wa         = models.BooleanField(default=True)

    # Payment Gateway Duitku
    duitku_merchant_code = models.CharField(max_length=50, blank=True)
    duitku_api_key       = models.CharField(max_length=100, blank=True)
    duitku_sandbox       = models.BooleanField(default=True)
    nama_rekening        = models.CharField(max_length=200, blank=True)
    bank_rekening        = models.CharField(max_length=50, blank=True)
    no_rekening          = models.CharField(max_length=50, blank=True)
    atas_nama            = models.CharField(max_length=200, blank=True)

     # ========== PANITIA PMB ==========
    nama_ketua_pmb     = models.CharField(max_length=200, blank=True, help_text="Nama lengkap dengan gelar — untuk TTD dokumen resmi (SK, undangan, dll)")
    nip_ketua_pmb      = models.CharField(max_length=30, blank=True, help_text="NIP / NIDN / ID identitas")
    ttd_ketua_pmb      = models.ImageField(upload_to='ttd/', blank=True, null=True, help_text="PNG transparan untuk TTD digital, max 1 MB")

    nama_bendahara_pmb = models.CharField(max_length=200, blank=True, help_text="Nama lengkap dengan gelar — untuk TTD kwitansi pembayaran")
    nip_bendahara_pmb  = models.CharField(max_length=30, blank=True, help_text="NIP / NIDN / ID identitas")
    ttd_bendahara_pmb  = models.ImageField(upload_to='ttd/', blank=True, null=True, help_text="PNG transparan untuk TTD digital, max 1 MB")
    
    class Meta:
        db_table    = 'pmb\".\"pengaturan_sistem'
        verbose_name = 'Pengaturan Sistem'
        verbose_name_plural = 'Pengaturan Sistem'

    def __str__(self):
        return f'Pengaturan PMB {self.tahun_akademik_aktif}'

    def save(self, *args, **kwargs):
        # Pastikan hanya ada 1 record pengaturan
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj