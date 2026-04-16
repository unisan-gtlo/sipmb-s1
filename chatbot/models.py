from django.db import models
from accounts.models import User


class KnowledgeBase(models.Model):
    KATEGORI_CHOICES = [
        ('jalur',     'Jalur Penerimaan'),
        ('biaya',     'Biaya & Pembayaran'),
        ('jadwal',    'Jadwal & Gelombang'),
        ('dokumen',   'Dokumen Persyaratan'),
        ('seleksi',   'Seleksi & Tes'),
        ('prodi',     'Program Studi'),
        ('fasilitas', 'Fasilitas Kampus'),
        ('kontak',    'Kontak PMB'),
        ('cara_daftar','Cara Mendaftar'),
        ('referral',  'Referral & Afiliasi'),
        ('rpl',       'Jalur RPL'),
        ('umum',      'Informasi Umum'),
    ]
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('nonaktif', 'Nonaktif'),
    ]

    kategori         = models.CharField(max_length=15, choices=KATEGORI_CHOICES, default='umum')
    pertanyaan       = models.TextField(help_text='Contoh pertanyaan yang memicu jawaban ini')
    kata_kunci       = models.TextField(help_text='Kata kunci trigger, pisah dengan koma')
    jawaban          = models.TextField(help_text='Jawaban yang sudah disiapkan admin')
    link_terkait     = models.URLField(blank=True, help_text='Link halaman yang relevan')
    urutan_prioritas = models.IntegerField(default=0)
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    tgl_update       = models.DateTimeField(auto_now=True)
    diupdate_oleh    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table    = 'pmb\".\"knowledge_base'
        ordering    = ['kategori', 'urutan_prioritas']
        verbose_name = 'Knowledge Base'
        verbose_name_plural = 'Knowledge Base'

    def __str__(self):
        return f'[{self.get_kategori_display()}] {self.pertanyaan[:60]}'


class PengaturanChatbot(models.Model):
    AI_PROVIDER_CHOICES = [
        ('claude', 'Anthropic Claude'),
        ('openai', 'OpenAI GPT'),
    ]
    JAM_CHOICES = [
        ('24jam',       'Aktif 24 Jam'),
        ('jam_tertentu','Jam Tertentu'),
    ]

    nama_bot         = models.CharField(max_length=100, default='SINTA')
    deskripsi_bot    = models.CharField(max_length=200, default='Asisten PMB UNISAN')
    foto_bot         = models.ImageField(upload_to='chatbot/', blank=True, null=True)
    pesan_sambutan   = models.TextField(default='Halo! Saya SINTA, asisten virtual PMB UNISAN. Ada yang bisa saya bantu?')
    pesan_fallback   = models.TextField(default='Maaf, saya belum bisa menjawab pertanyaan itu. Silakan hubungi panitia PMB.')
    pesan_eskalasi   = models.TextField(default='Pertanyaan Anda akan diteruskan ke panitia PMB. Silakan tunggu.')
    ai_provider      = models.CharField(max_length=10, choices=AI_PROVIDER_CHOICES, default='claude')
    ai_model         = models.CharField(max_length=50, default='claude-sonnet-4-6')
    system_prompt    = models.TextField(blank=True)
    max_token        = models.IntegerField(default=500)
    aktif            = models.BooleanField(default=True)
    jam_operasional  = models.CharField(max_length=15, choices=JAM_CHOICES, default='24jam')
    jam_buka         = models.TimeField(null=True, blank=True)
    jam_tutup        = models.TimeField(null=True, blank=True)
    pesan_diluar_jam = models.TextField(default='Chatbot sedang tidak aktif. Silakan hubungi panitia PMB.')

    class Meta:
        db_table    = 'pmb\".\"pengaturan_chatbot'
        verbose_name = 'Pengaturan Chatbot'
        verbose_name_plural = 'Pengaturan Chatbot'

    def __str__(self):
        return f'Pengaturan Chatbot — {self.nama_bot}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SesiChat(models.Model):
    STATUS_CHOICES = [
        ('aktif',    'Aktif'),
        ('selesai',  'Selesai'),
        ('eskalasi', 'Eskalasi ke Manusia'),
    ]

    session_id          = models.CharField(max_length=100, unique=True)
    user                = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    nama_tamu           = models.CharField(max_length=100, blank=True)
    ip_address          = models.GenericIPAddressField(null=True, blank=True)
    tgl_mulai           = models.DateTimeField(auto_now_add=True)
    tgl_terakhir        = models.DateTimeField(auto_now=True)
    total_pesan         = models.IntegerField(default=0)
    status              = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')
    eskalasi_ke_manusia = models.BooleanField(default=False)

    class Meta:
        db_table    = 'pmb\".\"sesi_chat'
        ordering    = ['-tgl_mulai']
        verbose_name = 'Sesi Chat'
        verbose_name_plural = 'Sesi Chat'

    def __str__(self):
        nama = self.user.nama_lengkap if self.user else self.nama_tamu or 'Tamu'
        return f'Chat {self.session_id[:8]} — {nama}'


class RiwayatChat(models.Model):
    PENGIRIM_CHOICES = [
        ('user', 'User'),
        ('bot',  'Bot / AI'),
    ]
    SUMBER_CHOICES = [
        ('knowledge_base', 'Knowledge Base'),
        ('ai',             'Claude AI'),
        ('fallback',       'Fallback'),
    ]

    sesi           = models.ForeignKey(SesiChat, on_delete=models.CASCADE, related_name='pesan')
    pengirim       = models.CharField(max_length=5, choices=PENGIRIM_CHOICES)
    pesan          = models.TextField()
    sumber_jawaban = models.CharField(max_length=15, choices=SUMBER_CHOICES, blank=True)
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.SET_NULL, null=True, blank=True)
    tgl_kirim      = models.DateTimeField(auto_now_add=True)
    helpful        = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table    = 'pmb\".\"riwayat_chat'
        ordering    = ['tgl_kirim']
        verbose_name = 'Riwayat Chat'
        verbose_name_plural = 'Riwayat Chat'

    def __str__(self):
        return f'{self.pengirim}: {self.pesan[:50]}'