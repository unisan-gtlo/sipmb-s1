from django.contrib import admin
from .models import (
    JalurPenerimaan, GelombangPenerimaan,
    ProdiPMB, PersyaratanJalur, PengaturanSistem
)


class PersyaratanInline(admin.TabularInline):
    model  = PersyaratanJalur
    extra  = 1
    fields = ['nama_dokumen', 'wajib', 'format_file', 'ukuran_max', 'urutan']


class ProdiPMBInline(admin.TabularInline):
    model  = ProdiPMB
    extra  = 1
    fields = ['kode_prodi', 'nama_prodi', 'kode_fakultas', 'kuota', 'biaya_kuliah', 'status']


@admin.register(JalurPenerimaan)
class JalurPenerimaanAdmin(admin.ModelAdmin):
    list_display = ['kode_jalur', 'nama_jalur', 'icon_preview', 'warna_badge', 'ada_tes', 'ada_wawancara', 'status', 'urutan']
    list_filter = ['status', 'warna', 'ada_tes', 'ada_wawancara']
    search_fields = ['kode_jalur', 'nama_jalur']
    list_editable = ['status', 'urutan']
    ordering = ['urutan']
    
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',)
        }

    fieldsets = (
        ('Data Utama', {
            'fields': ('kode_jalur', 'nama_jalur', 'deskripsi', 'syarat_umum')
        }),
        ('Seleksi', {
            'fields': ('ada_tes', 'ada_wawancara')
        }),
        ('Tampilan di Web', {
            'fields': ('icon', 'warna'),
            'description': (
                '<b>Icon:</b> Gunakan Bootstrap Icons. Contoh populer:<br>'
                '• <code>bi-pencil-square</code> — pensil (Reguler)<br>'
                '• <code>bi-trophy-fill</code> — trofi (Prestasi/Undangan)<br>'
                '• <code>bi-mortarboard-fill</code> — topi wisuda (Beasiswa)<br>'
                '• <code>bi-arrow-left-right</code> — panah (Pindahan)<br>'
                '• <code>bi-building-fill</code> — gedung (Kemitraan)<br>'
                '• <code>bi-star-fill</code>, <code>bi-award-fill</code>, <code>bi-heart-fill</code><br>'
                'Daftar lengkap: <a href="https://icons.getbootstrap.com/" target="_blank">icons.getbootstrap.com</a>'
            )
        }),
        ('Status & Urutan', {
            'fields': ('status', 'urutan')
        }),
    )
    
    def icon_preview(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<i class="bi {}" style="font-size:20px;color:#667eea"></i> <code>{}</code>',
            obj.icon, obj.icon
        )
    icon_preview.short_description = 'Preview Icon'
    
    def warna_badge(self, obj):
        from django.utils.html import format_html
        color_map = {
            'purple': '#764ba2', 'blue': '#1d4ed8', 'green': '#059669',
            'orange': '#d97706', 'red': '#dc2626', 'teal': '#0d9488',
            'pink': '#db2777', 'indigo': '#4f46e5', 'yellow': '#ca8a04',
            'cyan': '#0891b2',
        }
        color = color_map.get(obj.warna, '#667eea')
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;background:{};color:white;border-radius:8px;font-size:12px;font-weight:600">{}</span>',
            color, obj.get_warna_display() if hasattr(obj, 'get_warna_display') else obj.warna
        )
    warna_badge.short_description = 'Warna'


@admin.register(GelombangPenerimaan)
class GelombangPenerimaanAdmin(admin.ModelAdmin):
    list_display  = ['nama_gelombang', 'jalur', 'tahun_akademik',
                     'tgl_buka', 'tgl_tutup', 'jenis_biaya', 'biaya_akhir', 'status']
    list_filter   = ['status', 'jenis_biaya', 'tahun_akademik', 'jalur']
    search_fields = ['nama_gelombang', 'tahun_akademik']
    ordering      = ['tahun_akademik', 'jalur', 'nama_gelombang']
    inlines       = [ProdiPMBInline]


@admin.register(ProdiPMB)
class ProdiPMBAdmin(admin.ModelAdmin):
    list_display  = ['nama_prodi', 'kode_fakultas', 'gelombang', 'kuota', 'biaya_kuliah', 'status']
    list_filter   = ['status', 'kode_fakultas', 'gelombang']
    search_fields = ['nama_prodi', 'kode_prodi', 'kode_fakultas']


@admin.register(PersyaratanJalur)
class PersyaratanJalurAdmin(admin.ModelAdmin):
    list_display  = ['nama_dokumen', 'jalur', 'wajib', 'format_file', 'ukuran_max', 'urutan']
    list_filter   = ['jalur', 'wajib', 'format_file']
    search_fields = ['nama_dokumen']
    ordering      = ['jalur', 'urutan']


@admin.register(PengaturanSistem)
class PengaturanSistemAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Info Akademik', {
            'fields': ('tahun_akademik_aktif', 'status_pendaftaran')
        }),
        ('Info Pejabat', {
            'fields': ('nama_rektor', 'nama_wakil_rektor')
        }),
         # ← TAMBAH DI SINI
        ('Info Panitia PMB', {
          'fields': (
            ('nama_ketua_pmb', 'nip_ketua_pmb'),
            'ttd_ketua_pmb',
            ('nama_bendahara_pmb', 'nip_bendahara_pmb'),
            'ttd_bendahara_pmb',
        ),
            'description': 'Nama & TTD digital untuk dokumen resmi. Nama Bendahara otomatis dipakai di kwitansi pembayaran.',
         }),

        ('Kontak PMB', {
            'fields': ('no_telepon_pmb', 'email_pmb', 'whatsapp_pmb', 'alamat_kampus')
        }),
        ('Tampilan', {
            'fields': ('logo', 'banner_utama', 'teks_sambutan')
        }),
        ('WhatsApp Group', {
            'fields': ('link_wa_group', 'nama_wa_group', 'deskripsi_wa_group', 'tampilkan_wa')
        }),
        ('Payment Gateway Duitku', {
            'fields': ('duitku_merchant_code', 'duitku_api_key', 'duitku_sandbox',
                       'nama_rekening', 'bank_rekening', 'no_rekening', 'atas_nama'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Hanya boleh ada 1 record pengaturan
        return not PengaturanSistem.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False