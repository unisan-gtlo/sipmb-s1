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
    list_display  = ['kode_jalur', 'nama_jalur', 'ada_tes', 'ada_wawancara', 'status', 'urutan']
    list_filter   = ['status', 'ada_tes', 'ada_wawancara']
    search_fields = ['kode_jalur', 'nama_jalur']
    ordering      = ['urutan']
    inlines       = [PersyaratanInline]


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