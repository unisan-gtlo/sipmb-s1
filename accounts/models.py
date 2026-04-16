from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin_pmb',       'Admin PMB'),
        ('operator_pmb',    'Operator PMB'),
        ('panitia_seleksi', 'Panitia Seleksi'),
        ('recruiter',       'Recruiter'),
        ('calon_maba',      'Calon Mahasiswa Baru'),
        ('pimpinan',        'Pimpinan'),
    ]

    JENIS_KELAMIN_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]

    role            = models.CharField(max_length=20, choices=ROLE_CHOICES, default='calon_maba')
    no_hp           = models.CharField(max_length=20, blank=True)
    jenis_kelamin   = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES, blank=True)
    foto            = models.ImageField(upload_to='foto_user/', blank=True, null=True)
    is_sso_user     = models.BooleanField(default=False)  # True = login via SSO (admin/operator)
    sso_uuid        = models.CharField(max_length=100, blank=True)  # UUID dari SSO
    tgl_dibuat      = models.DateTimeField(auto_now_add=True)
    tgl_diupdate    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'pmb\".\"auth_user'  # eksplisit schema pmb
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'

    @property
    def is_admin_pmb(self):
        return self.role == 'admin_pmb'

    @property
    def is_operator(self):
        return self.role == 'operator_pmb'

    @property
    def is_calon_maba(self):
        return self.role == 'calon_maba'

    @property
    def is_recruiter(self):
        return self.role == 'recruiter'

    @property
    def is_pimpinan(self):
        return self.role == 'pimpinan'

    @property
    def is_panitia(self):
        return self.role == 'panitia_seleksi'

    @property
    def nama_lengkap(self):
        return self.get_full_name() or self.username