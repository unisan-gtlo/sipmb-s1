from django.contrib import admin
from .models import Pendaftaran, LogStatusPendaftaran, ProfilPendaftar, TokenAktivasi


class LogStatusInline(admin.TabularInline):
    model   = LogStatusPendaftaran
    extra   = 0
    readonly_fields = ['status_lama', 'status_baru', 'keterangan', 'diubah_oleh', 'tgl_perubahan']
    can_delete = False


class ProfilInline(admin.StackedInline):
    model  = ProfilPendaftar
    extra  = 0
    can_delete = False


@admin.register(Pendaftaran)
class PendaftaranAdmin(admin.ModelAdmin):
    list_display  = ['no_pendaftaran', 'nama_lengkap', 'jalur', 'gelombang', 'status', 'tgl_daftar']
    list_filter   = ['status', 'jalur', 'gelombang']
    search_fields = ['no_pendaftaran', 'user__first_name', 'user__last_name', 'user__email']
    ordering      = ['-tgl_daftar']
    readonly_fields = ['no_pendaftaran', 'tgl_daftar']
    inlines       = [ProfilInline, LogStatusInline]


@admin.register(ProfilPendaftar)
class ProfilPendaftarAdmin(admin.ModelAdmin):
    list_display  = ['pendaftaran', 'nik', 'asal_sekolah', 'tahun_lulus', 'get_persen_lengkap']
    search_fields = ['nik', 'asal_sekolah', 'pendaftaran__no_pendaftaran']

    def get_persen_lengkap(self, obj):
        return f'{obj.persen_lengkap}%'
    get_persen_lengkap.short_description = 'Kelengkapan'


@admin.register(TokenAktivasi)
class TokenAktivasiAdmin(admin.ModelAdmin):
    list_display  = ['user', 'token', 'sudah_aktif', 'tgl_dibuat', 'tgl_aktif']
    list_filter   = ['sudah_aktif']
    readonly_fields = ['token', 'tgl_dibuat', 'tgl_aktif']