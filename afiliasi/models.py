from django.db import models
from accounts.models import User
from pendaftaran.models import Pendaftaran


class Recruiter(models.Model):
    """Agen/recruiter yang mendaftarkan calon mahasiswa"""
    STATUS_CHOICES = [
        ('menunggu', 'Menunggu Verifikasi'),
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
        ('suspend',  'Suspend'),
    ]
    LEVEL_CHOICES = [
        (1, 'Level 1 — Recruiter'),
        (2, 'Level 2 — Senior Recruiter'),
        (3, 'Level 3 — Master Recruiter'),
        (4, 'Level 4 — Diamond Recruiter'),
    ]

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter')
    kode_referral   = models.CharField(max_length=20, unique=True)
    level           = models.IntegerField(choices=LEVEL_CHOICES, default=1)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='menunggu')
    rekruiter_induk = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='downline', help_text='Recruiter yang merekrut recruiter ini'
    )
    bank            = models.CharField(max_length=50, blank=True)
    no_rekening     = models.CharField(max_length=30, blank=True)
    nama_rekening   = models.CharField(max_length=100, blank=True)
    total_referral  = models.IntegerField(default=0)
    total_komisi    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tgl_bergabung   = models.DateTimeField(auto_now_add=True)
    catatan         = models.TextField(blank=True)
    foto_selfie = models.ImageField(upload_to='recruiter/selfie/', blank=True, null=True)
    foto_ktp    = models.ImageField(upload_to='recruiter/ktp/',    blank=True, null=True)
    pekerjaan   = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table     = 'pmb\".\"recruiter'
        verbose_name = 'Recruiter'
        verbose_name_plural = 'Recruiter'

    def __str__(self):
        return f'{self.user.get_full_name()} [{self.kode_referral}]'

    def hitung_komisi_per_referral(self):
        """Komisi per pendaftar yang lulus administrasi berdasarkan level"""
        komisi_map = {1: 50000, 2: 75000, 3: 100000, 4: 150000}
        return komisi_map.get(self.level, 50000)


class KomisiReferral(models.Model):
    """Catatan komisi per pendaftaran yang berhasil"""
    STATUS_CHOICES = [
        ('pending',   'Menunggu Verifikasi'),
        ('approved',  'Disetujui'),
        ('paid',      'Sudah Dibayar'),
        ('rejected',  'Ditolak'),
    ]

    recruiter       = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='komisi')
    pendaftaran     = models.ForeignKey(Pendaftaran, on_delete=models.CASCADE, related_name='komisi')
    jumlah_komisi   = models.DecimalField(max_digits=10, decimal_places=2)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tgl_komisi      = models.DateTimeField(auto_now_add=True)
    tgl_approved    = models.DateTimeField(null=True, blank=True)
    tgl_paid        = models.DateTimeField(null=True, blank=True)
    diproses_oleh   = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='komisi_diproses'
    )
    catatan         = models.TextField(blank=True)
    keterangan_tolak= models.TextField(blank=True)

    class Meta:
        db_table     = 'pmb\".\"komisi_referral'
        verbose_name = 'Komisi Referral'
        verbose_name_plural = 'Komisi Referral'

    def __str__(self):
        return f'Komisi {self.recruiter.kode_referral} — {self.pendaftaran.no_pendaftaran}'


class PencairanKomisi(models.Model):
    """Pencairan komisi ke rekening recruiter"""
    STATUS_CHOICES = [
        ('pending',   'Menunggu'),
        ('proses',    'Diproses'),
        ('selesai',   'Selesai'),
        ('gagal',     'Gagal'),
    ]

    recruiter       = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='pencairan')
    jumlah          = models.DecimalField(max_digits=12, decimal_places=2)
    bank            = models.CharField(max_length=50)
    no_rekening     = models.CharField(max_length=30)
    nama_rekening   = models.CharField(max_length=100)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tgl_request     = models.DateTimeField(auto_now_add=True)
    tgl_proses      = models.DateTimeField(null=True, blank=True)
    bukti_transfer  = models.ImageField(upload_to='bukti_transfer/', null=True, blank=True)
    diproses_oleh   = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pencairan_diproses'
    )
    catatan         = models.TextField(blank=True)

    class Meta:
        db_table     = 'pmb\".\"pencairan_komisi'
        verbose_name = 'Pencairan Komisi'
        verbose_name_plural = 'Pencairan Komisi'

    def __str__(self):
        return f'Pencairan {self.recruiter.kode_referral} — Rp {self.jumlah:,.0f}'


class PengaturanAfiliasi(models.Model):
    """Pengaturan sistem afiliasi"""
    komisi_level_1      = models.DecimalField(max_digits=10, decimal_places=2, default=50000)
    komisi_level_2      = models.DecimalField(max_digits=10, decimal_places=2, default=75000)
    komisi_level_3      = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    komisi_level_4      = models.DecimalField(max_digits=10, decimal_places=2, default=150000)
    min_pencairan       = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    syarat_naik_level_2 = models.IntegerField(default=5,  help_text='Jumlah referral untuk naik ke level 2')
    syarat_naik_level_3 = models.IntegerField(default=15, help_text='Jumlah referral untuk naik ke level 3')
    syarat_naik_level_4 = models.IntegerField(default=30, help_text='Jumlah referral untuk naik ke level 4')
    aktif               = models.BooleanField(default=True)
    deskripsi_program   = models.TextField(blank=True)

    class Meta:
        db_table     = 'pmb\".\"pengaturan_afiliasi'
        verbose_name = 'Pengaturan Afiliasi'

    def __str__(self):
        return 'Pengaturan Afiliasi'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj