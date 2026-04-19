from django.db import models
from accounts.models import User
from master.models import JalurPenerimaan, GelombangPenerimaan, ProdiPMB
import uuid
from utils.validators import validate_image, validate_document_or_image

def generate_no_pendaftaran(status_masuk='PDB', tahun=None):
    """
    Generate nomor pendaftaran format: YYYY-XX-NNNN
    
    XX = 01 (PDB) atau 02 (PINDAHAN)
    NNNN = counter per status_masuk per tahun (mulai 0001)
    
    Contoh:
      2026-01-0001  → PDB pendaftar pertama
      2026-02-0001  → PINDAHAN pendaftar pertama
      2026-01-0002  → PDB pendaftar kedua
    """
    import datetime
    from django.apps import apps
    
    tahun = tahun or datetime.datetime.now().year
    
    # Mapping status ke kode numerik
    KODE_STATUS = {
        'PDB':      '01',
        'PINDAHAN': '02',
    }
    kode = KODE_STATUS.get(status_masuk, '01')
    
    prefix = f'{tahun}-{kode}-'
    
    # Lookup model via apps (avoid circular import)
    Pendaftaran = apps.get_model('pendaftaran', 'Pendaftaran')
    
    # Cari nomor terakhir untuk prefix ini
    last = Pendaftaran.objects.filter(
        no_pendaftaran__startswith=prefix
    ).order_by('-no_pendaftaran').first()
    
    if last:
        try:
            last_seq = int(last.no_pendaftaran.split('-')[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1
    
    return f'{prefix}{next_seq:04d}'


class Pendaftaran(models.Model):
    STATUS_CHOICES = [
        ('DRAFT',            'Draft'),
        ('LENGKAP',          'Lengkap'),
        ('DIVERIFIKASI',     'Diverifikasi'),
        ('LULUS_ADM',        'Lulus Administrasi'),
        ('TIDAK_LULUS_ADM',  'Tidak Lulus Administrasi'),
        ('TERJADWAL',        'Terjadwal Seleksi'),
        ('LULUS_SELEKSI',    'Lulus Seleksi'),
        ('TIDAK_LULUS',      'Tidak Lulus'),
        ('DAFTAR_ULANG',     'Daftar Ulang'),
        ('AKTIF',            'Aktif Mahasiswa'),
        ('MENGUNDURKAN_DIRI','Mengundurkan Diri'),
    ]

    # Identitas pendaftaran
    no_pendaftaran  = models.CharField(max_length=30, unique=True, default=generate_no_pendaftaran)
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pendaftaran')
    jalur           = models.ForeignKey(JalurPenerimaan, on_delete=models.PROTECT)
    gelombang       = models.ForeignKey(GelombangPenerimaan, on_delete=models.PROTECT)
    prodi_pilihan_1 = models.ForeignKey(ProdiPMB, on_delete=models.PROTECT, related_name='pilihan_1')
    prodi_pilihan_2 = models.ForeignKey(ProdiPMB, on_delete=models.PROTECT, related_name='pilihan_2', null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # Kode referral & voucher
    kode_referral   = models.CharField(max_length=20, blank=True)
    kode_voucher    = models.CharField(max_length=20, blank=True)

    # Timestamps
    tgl_daftar      = models.DateTimeField(auto_now_add=True)
    tgl_diupdate    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = 'pmb\".\"pendaftaran'
        ordering    = ['-tgl_daftar']
        verbose_name = 'Pendaftaran'
        verbose_name_plural = 'Pendaftaran'

    def save(self, *args, **kwargs):
        """
        Override save untuk:
        1. Auto-determine status_masuk dari jalur.kode_jalur
        2. Generate no_pendaftaran dengan format YYYY-XX-NNNN kalau belum ada
        3. Sync status_masuk ke profil setelah save
        """
        # Tentukan status_masuk dari jalur
        status_masuk = 'PDB'
        if self.jalur_id:
            try:
                kode_jalur = (self.jalur.kode_jalur or '').upper()
                if 'PINDAH' in kode_jalur:
                    status_masuk = 'PINDAHAN'
            except Exception:
                pass
        
        # Generate no_pendaftaran dengan format baru kalau belum ada
        if not self.no_pendaftaran:
            self.no_pendaftaran = generate_no_pendaftaran(status_masuk=status_masuk)
        
        super().save(*args, **kwargs)
        
        # Sync status_masuk ke profil (setelah Pendaftaran punya ID)
        try:
            profil = self.profil
            if profil.status_masuk != status_masuk:
                profil.status_masuk = status_masuk
                profil.save(update_fields=['status_masuk'])
        except Exception:
            pass
    
    def __str__(self):
        return f'{self.no_pendaftaran} — {self.user.nama_lengkap}'

    @property
    def nama_lengkap(self):
        return self.user.get_full_name()

    @property
    def is_lengkap(self):
        """Cek apakah profil & dokumen sudah lengkap"""
        try:
            profil = self.profil
            return profil.is_lengkap
        except:
            return False


class LogStatusPendaftaran(models.Model):
    pendaftaran  = models.ForeignKey(Pendaftaran, on_delete=models.CASCADE, related_name='log_status')
    status_lama  = models.CharField(max_length=20, blank=True)
    status_baru  = models.CharField(max_length=20)
    keterangan   = models.TextField(blank=True)
    diubah_oleh  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tgl_perubahan= models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table    = 'pmb\".\"log_status_pendaftaran'
        ordering    = ['-tgl_perubahan']
        verbose_name = 'Log Status Pendaftaran'
        verbose_name_plural = 'Log Status Pendaftaran'

    def __str__(self):
        return f'{self.pendaftaran.no_pendaftaran} — {self.status_lama} → {self.status_baru}'


class ProfilPendaftar(models.Model):
    JENIS_KELAMIN_CHOICES = [('L', 'Laki-laki'), ('P', 'Perempuan')]
    STATUS_NIKAH_CHOICES = [
        ('belum_menikah', 'Belum Menikah'),
        ('menikah',       'Menikah'),
    ]
    KEWARGANEGARAAN_CHOICES = [
        ('WNI', 'WNI'),
        ('WNA', 'WNA'),
    ]
    SUMBER_INFO_CHOICES = [
        ('website',   'Website PMB UNISAN'),
        ('instagram', 'Instagram'),
        ('facebook',  'Facebook'),
        ('tiktok',    'TikTok'),
        ('youtube',   'YouTube'),
        ('whatsapp',  'WhatsApp / Grup WA'),
        ('teman',     'Info dari Teman / Keluarga'),
        ('guru',      'Info dari Guru / Sekolah'),
        ('panitia',   'Konseling Langsung Panitia'),
        ('brosur',    'Brosur / Flyer'),
        ('spanduk',   'Spanduk / Banner'),
        ('recruiter', 'Recruiter / Referral'),
        ('lainnya',   'Lainnya'),
    ]

    UKURAN_BAJU_CHOICES = [
        ('S',   'S'),
        ('M',   'M'),
        ('L',   'L'),
        ('XL',  'XL'),
        ('XXL', 'XXL'),
        ('3XL', '3XL'),
        ]

    PENDIDIKAN_ORTU_CHOICES = [
        ('SD',           'SD / Sederajat'),
        ('SMP',          'SMP / Sederajat'),
        ('SMA',          'SMA / SMK / Sederajat'),
        ('D3',           'Diploma (D1/D2/D3)'),
        ('D4',           'D4 / Sarjana Terapan'),
        ('S1',           'S1 / Sarjana'),
        ('S2',           'S2 / Magister'),
        ('S3',           'S3 / Doktor'),
        ('TIDAK_SEKOLAH','Tidak Sekolah'),
    ]

    STATUS_MASUK_CHOICES = [
        ('PDB',      'Penerimaan Mahasiswa Baru'),
        ('PINDAHAN', 'Mahasiswa Pindahan'),
    ]

    ukuran_baju = models.CharField(
        max_length=5, choices=UKURAN_BAJU_CHOICES, blank=True,
        help_text='Ukuran baju untuk kebutuhan almamater/seragam'
    )

    pendaftaran     = models.OneToOneField(Pendaftaran, on_delete=models.CASCADE, related_name='profil')
    # Status masuk (auto-set dari jalur pendaftaran)
    status_masuk    = models.CharField(
        max_length=10,
        choices=STATUS_MASUK_CHOICES,
        default='PDB',
        verbose_name='Status Masuk'
    )
    # Data diri
    nik             = models.CharField(max_length=16, blank=True)
    tempat_lahir    = models.CharField(max_length=100, blank=True)
    tgl_lahir       = models.DateField(null=True, blank=True)
    jenis_kelamin   = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES, blank=True)
    agama_id        = models.BigIntegerField(null=True, blank=True)
    agama_nama      = models.CharField(max_length=20, blank=True)
    kewarganegaraan = models.CharField(max_length=3, choices=KEWARGANEGARAAN_CHOICES, default='WNI')
    status_nikah    = models.CharField(max_length=15, choices=STATUS_NIKAH_CHOICES, default='belum_menikah')
    kebutuhan_khusus= models.CharField(max_length=100, blank=True)
    foto            = models.ImageField(upload_to='foto_pendaftar/', blank=True, null=True)
    validators=[validate_image],
    # Alamat
    alamat_lengkap      = models.TextField(blank=True)
    provinsi_id         = models.BigIntegerField(null=True, blank=True)
    provinsi_nama       = models.CharField(max_length=100, blank=True)
    kabupaten_kota_id   = models.BigIntegerField(null=True, blank=True)
    kabupaten_kota_nama = models.CharField(max_length=100, blank=True)
    kecamatan_id        = models.BigIntegerField(null=True, blank=True)
    kecamatan_nama      = models.CharField(max_length=100, blank=True)
    kelurahan           = models.CharField(max_length=100, blank=True)
    kode_pos            = models.CharField(max_length=10, blank=True)

    # Data orang tua
    nama_ayah       = models.CharField(max_length=200, blank=True)
    pekerjaan_ayah  = models.CharField(max_length=100, blank=True)
    # Tambahkan setelah field pekerjaan_ayah
    pendidikan_ayah = models.CharField(
        max_length=20, choices=PENDIDIKAN_ORTU_CHOICES,
        blank=True, default='',
        verbose_name='Pendidikan Terakhir Ayah'
    )
    no_hp_ayah = models.CharField(
        max_length=20, blank=True, default='',
        verbose_name='No HP Ayah'
    )
    penghasilan_ayah= models.CharField(max_length=20, blank=True)
    nama_ibu        = models.CharField(max_length=200, blank=True)
    pekerjaan_ibu   = models.CharField(max_length=100, blank=True)
    pendidikan_ibu  = models.CharField(
        max_length=20, choices=PENDIDIKAN_ORTU_CHOICES,
        blank=True, default='',
        verbose_name='Pendidikan Terakhir Ibu'
    )
    no_hp_ibu = models.CharField(
        max_length=20, blank=True, default='',
        verbose_name='No HP Ibu'
    )
    penghasilan_ibu = models.CharField(max_length=20, blank=True)
    nama_wali       = models.CharField(max_length=200, blank=True)
    no_hp_ortu      = models.CharField(max_length=20, blank=True)
    alamat_ortu     = models.TextField(blank=True)

    # Data pendidikan
    sekolah_id      = models.BigIntegerField(null=True, blank=True)
    asal_sekolah    = models.CharField(max_length=200, blank=True)
    npsn            = models.CharField(max_length=10, blank=True)
    jurusan_id      = models.CharField(max_length=20, blank=True)
    jurusan_sekolah = models.CharField(max_length=200, blank=True)
    tahun_lulus     = models.IntegerField(null=True, blank=True)
    no_ijazah       = models.CharField(max_length=100, blank=True)
    nilai_rata_rata = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    prestasi        = models.TextField(blank=True)

    # Sumber informasi
    sumber_informasi      = models.CharField(max_length=20, choices=SUMBER_INFO_CHOICES, blank=True)
    sumber_informasi_lain = models.CharField(max_length=200, blank=True)

    tgl_diupdate    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'pmb\".\"profil_pendaftar'
        verbose_name = 'Profil Pendaftar'
        verbose_name_plural = 'Profil Pendaftar'

    
    def __str__(self):
        return f'Profil — {self.pendaftaran.no_pendaftaran}'

    @property
    def is_lengkap(self):
        wajib = [
            self.nik, self.tempat_lahir, self.tgl_lahir,
            self.jenis_kelamin, self.agama_nama, self.alamat_lengkap,
            self.nama_ayah, self.nama_ibu, self.asal_sekolah,
            self.tahun_lulus,
        ]
        return all(bool(v) for v in wajib)

    @property
    def persen_lengkap(self):
        def terisi(val):
            if val is None:
                return False
            if isinstance(val, str):
                return val.strip() != ''
            return True

        semua = [
            self.nik,
            self.tempat_lahir,
            self.tgl_lahir,
            self.jenis_kelamin,
            self.agama_nama,
            self.alamat_lengkap,
            self.provinsi_nama,
            self.kabupaten_kota_nama,
            self.kode_pos,
            self.nama_ayah,
            self.pekerjaan_ayah,
            self.nama_ibu,
            self.pekerjaan_ibu,
            self.no_hp_ortu,
            self.asal_sekolah,
            self.jurusan_sekolah,
            self.tahun_lulus,
            self.no_ijazah,
            self.nilai_rata_rata,
            self.foto,
        ]
        jumlah_terisi = sum(1 for f in semua if terisi(f))
        return int((jumlah_terisi / len(semua)) * 100)

class TokenAktivasi(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='token_aktivasi')
    token      = models.UUIDField(default=uuid.uuid4, unique=True)
    tgl_dibuat = models.DateTimeField(auto_now_add=True)
    sudah_aktif= models.BooleanField(default=False)
    tgl_aktif  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table    = 'pmb\".\"token_aktivasi'
        verbose_name = 'Token Aktivasi'
        verbose_name_plural = 'Token Aktivasi'

    def __str__(self):
        return f'Token — {self.user.username}'

    @property
    def is_expired(self):
        """Token expired setelah 24 jam"""
        from django.utils import timezone
        import datetime
        return timezone.now() > self.tgl_dibuat + datetime.timedelta(hours=24)