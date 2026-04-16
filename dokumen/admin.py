from django.contrib import admin
from .models import DokumenPendaftar


@admin.register(DokumenPendaftar)
class DokumenPendaftarAdmin(admin.ModelAdmin):
    list_display  = ['pendaftaran', 'nama_dokumen', 'status_verifikasi', 'tgl_upload', 'diverifikasi_oleh']
    list_filter   = ['status_verifikasi', 'persyaratan__jalur']
    search_fields = ['pendaftaran__no_pendaftaran', 'pendaftaran__user__first_name']
    ordering      = ['-tgl_upload']
    readonly_fields = ['tgl_upload', 'tgl_verifikasi']

    actions = ['verifikasi_dokumen', 'tolak_dokumen']

    def verifikasi_dokumen(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status_verifikasi='terverifikasi',
            tgl_verifikasi=timezone.now(),
            diverifikasi_oleh=request.user
        )
        self.message_user(request, f'{queryset.count()} dokumen berhasil diverifikasi.')
    verifikasi_dokumen.short_description = 'Verifikasi dokumen terpilih'

    def tolak_dokumen(self, request, queryset):
        queryset.update(status_verifikasi='ditolak')
        self.message_user(request, f'{queryset.count()} dokumen ditolak.')
    tolak_dokumen.short_description = 'Tolak dokumen terpilih'