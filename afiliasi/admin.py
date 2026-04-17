from django.contrib import admin
from django.utils import timezone
from .models import Recruiter, KomisiReferral, PencairanKomisi, PengaturanAfiliasi



@admin.register(KomisiReferral)
class KomisiReferralAdmin(admin.ModelAdmin):
    list_display  = ['recruiter', 'pendaftaran', 'jumlah_komisi', 'status', 'tgl_komisi']
    list_filter   = ['status']
    readonly_fields = ['tgl_komisi']


@admin.register(PencairanKomisi)
class PencairanKomisiAdmin(admin.ModelAdmin):
    list_display  = ['recruiter', 'jumlah', 'bank', 'status', 'tgl_request']
    list_filter   = ['status']
    readonly_fields = ['tgl_request']


@admin.register(PengaturanAfiliasi)
class PengaturanAfiliasiAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not PengaturanAfiliasi.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display    = ['user', 'kode_referral', 'level', 'status',
                       'pekerjaan', 'total_referral', 'tgl_bergabung']
    list_filter     = ['level', 'status']
    search_fields   = ['user__first_name', 'user__last_name', 'kode_referral']
    readonly_fields = ['total_referral', 'total_komisi', 'tgl_bergabung',
                       'foto_selfie_preview', 'foto_ktp_preview']
    actions         = ['approve_recruiter', 'suspend_recruiter']

    def foto_selfie_preview(self, obj):
        from django.utils.html import format_html
        if obj.foto_selfie:
            return format_html(
                '<img src="{}" style="width:150px;border-radius:8px">',
                obj.foto_selfie.url
            )
        return '-'
    foto_selfie_preview.short_description = 'Preview Selfie'

    def foto_ktp_preview(self, obj):
        from django.utils.html import format_html
        if obj.foto_ktp:
            return format_html(
                '<img src="{}" style="width:250px;border-radius:8px">',
                obj.foto_ktp.url
            )
        return '-'
    foto_ktp_preview.short_description = 'Preview KTP'

    def approve_recruiter(self, request, queryset):
        queryset.filter(status='menunggu').update(status='aktif')
        self.message_user(request, f'{queryset.count()} recruiter berhasil diaktifkan.')
    approve_recruiter.short_description = '✅ Approve & Aktifkan'

    def suspend_recruiter(self, request, queryset):
        queryset.update(status='suspend')
        self.message_user(request, f'{queryset.count()} recruiter di-suspend.')
    suspend_recruiter.short_description = '🚫 Suspend'