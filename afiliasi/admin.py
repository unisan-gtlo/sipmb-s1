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

# ============================================================
# FLYER GENERATOR ADMIN
# ============================================================

from django.utils.html import format_html
from django.core.cache import cache
from .models import KontenFlyer, TemplateFlyer


@admin.register(KontenFlyer)
class KontenFlyerAdmin(admin.ModelAdmin):
    list_display = (
        'nama_periode', 'tahun_akademik', 'status_badge', 'diubah_pada',
    )
    list_filter = ('is_aktif', 'tahun_akademik')
    search_fields = ('nama_periode', 'headline_utama')
    readonly_fields = ('dibuat_pada', 'diubah_pada', 'preview_warna')

    fieldsets = (
        ('Identitas Periode', {
            'fields': ('nama_periode', 'tahun_akademik', 'is_aktif'),
        }),
        ('Konten Teks', {
            'fields': ('headline_utama', 'sub_headline', 'cta_text'),
            'description': 'Konten ini akan muncul di flyer semua recruiter.',
        }),
        ('Statistik Kampus', {
            'fields': ('jumlah_fakultas', 'jumlah_prodi', 'jalur_tersedia'),
        }),
        ('Warna Tema', {
            'fields': ('warna_primer', 'warna_sekunder', 'warna_aksen', 'preview_warna'),
            'description': 'Format: #RRGGBB (contoh: #3C3489)',
        }),
        ('Footer', {
            'fields': ('website_display', 'nomor_wa_pmb'),
        }),
        ('Metadata', {
            'fields': ('dibuat_pada', 'diubah_pada'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        if obj.is_aktif:
            return format_html(
                '<span style="background:#22c55e;color:white;'
                'padding:3px 10px;border-radius:4px;font-size:11px;'
                'font-weight:500;">{}</span>',
                'AKTIF'
            )
        return format_html(
            '<span style="background:#9ca3af;color:white;'
            'padding:3px 10px;border-radius:4px;font-size:11px;">{}</span>',
            'nonaktif'
        )
    status_badge.short_description = 'Status'

    def preview_warna(self, obj):
        return format_html(
            '<div style="display:flex;gap:8px;">'
            '<div style="width:60px;height:60px;background:{};border-radius:8px;'
            'border:1px solid #ddd;" title="Primer"></div>'
            '<div style="width:60px;height:60px;background:{};border-radius:8px;'
            'border:1px solid #ddd;" title="Sekunder"></div>'
            '<div style="width:60px;height:60px;background:{};border-radius:8px;'
            'border:1px solid #ddd;" title="Aksen"></div>'
            '</div>',
            obj.warna_primer, obj.warna_sekunder, obj.warna_aksen
        )
    preview_warna.short_description = 'Preview Warna'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Invalidate cache flyer saat konten diubah
        try:
            cache.clear()
        except Exception:
            pass
        self.message_user(
            request,
            f"Konten '{obj.nama_periode}' tersimpan. "
            "Cache flyer di-refresh untuk semua recruiter."
        )


@admin.register(TemplateFlyer)
class TemplateFlyerAdmin(admin.ModelAdmin):
    list_display = (
        'urutan', 'nama', 'kode', 'ukuran_display', 'aspect_ratio',
        'is_aktif',
    )
    list_editable = ('is_aktif',)
    list_filter = ('is_aktif',)
    readonly_fields = ('kode',)
    ordering = ('urutan',)

    def ukuran_display(self, obj):
        return f"{obj.width} x {obj.height} px"
    ukuran_display.short_description = 'Ukuran'

    def has_add_permission(self, request):
        # 4 template sudah cukup, tidak perlu tambah
        return False

    def has_delete_permission(self, request, obj=None):
        return False
