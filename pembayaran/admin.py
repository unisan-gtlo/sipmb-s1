# pembayaran/admin.py
from django.contrib import admin
from .models import RekeningTujuan, Tagihan, KonfirmasiPembayaran
from .models import TransaksiDuitku
from .models import KodeVoucher

@admin.register(RekeningTujuan)
class RekeningTujuanAdmin(admin.ModelAdmin):
    list_display = ('nama_bank', 'no_rekening', 'atas_nama', 'urutan', 'aktif')
    list_editable = ('urutan', 'aktif')
    list_filter = ('aktif', 'nama_bank')
    search_fields = ('nama_bank', 'no_rekening', 'atas_nama')


class KonfirmasiInline(admin.TabularInline):
    model = KonfirmasiPembayaran
    extra = 0
    readonly_fields = ('created_at', 'tgl_konfirmasi', 'dikonfirmasi_oleh')
    fields = ('metode_bayar', 'jumlah_bayar', 'tgl_bayar', 'bukti_bayar', 'status', 'dikonfirmasi_oleh', 'tgl_konfirmasi')


@admin.register(Tagihan)
class TagihanAdmin(admin.ModelAdmin):
    list_display = ('kode_bayar', 'pendaftaran', 'jenis', 'jumlah', 'status', 'tgl_jatuh_tempo', 'created_at')
    list_filter = ('status', 'jenis', 'tgl_tagihan')
    search_fields = ('kode_bayar', 'pendaftaran__no_pendaftaran', 'pendaftaran__user__email')
    readonly_fields = ('kode_bayar', 'created_at', 'updated_at')
    inlines = [KonfirmasiInline]
    date_hierarchy = 'tgl_tagihan'


@admin.register(KonfirmasiPembayaran)
class KonfirmasiPembayaranAdmin(admin.ModelAdmin):
    list_display = ('tagihan', 'metode_bayar', 'jumlah_bayar', 'tgl_bayar', 'status', 'dikonfirmasi_oleh')
    list_filter = ('status', 'metode_bayar', 'tgl_bayar')
    search_fields = ('tagihan__kode_bayar', 'tagihan__pendaftaran__no_pendaftaran', 'atas_nama_pengirim', 'no_transaksi')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('tagihan', 'rekening_tujuan')




@admin.register(TransaksiDuitku)
class TransaksiDuitkuAdmin(admin.ModelAdmin):
    list_display = ('merchant_order_id', 'tagihan', 'payment_method', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('merchant_order_id', 'reference', 'tagihan__kode_bayar')
    readonly_fields = ('merchant_order_id', 'reference', 'signature', 'callback_payload',
                       'created_at', 'updated_at')
    raw_id_fields = ('tagihan',)

@admin.register(KodeVoucher)
class KodeVoucherAdmin(admin.ModelAdmin):
    list_display = (
        'kode_voucher',
        'jenis_diskon',
        'nilai_diskon_display',
        'periode_display',
        'kuota_display',
        'jalur',
        'status_badge',
    )
    list_filter = ('status', 'jenis_diskon', 'jalur')
    search_fields = ('kode_voucher', 'keterangan')
    readonly_fields = (
        'sudah_dipakai',
        'dibuat_oleh',
        'tgl_dibuat',
        'tgl_diupdate',
    )
    fieldsets = (
        ('Informasi Voucher', {
            'fields': ('kode_voucher', 'status', 'keterangan'),
        }),
        ('Diskon', {
            'fields': ('jenis_diskon', 'nilai_diskon'),
            'description': (
                'Untuk Persen: isi nilai 0-100 (mis. 100 = gratis, 50 = potongan 50%). '
                'Untuk Nominal: isi nilai dalam rupiah (mis. 50000 = potongan Rp 50.000).'
            ),
        }),
        ('Periode & Kuota', {
            'fields': ('berlaku_dari', 'berlaku_sampai', 'max_penggunaan', 'sudah_dipakai'),
            'description': 'Max penggunaan: 0 berarti tidak terbatas.',
        }),
        ('Pembatasan Jalur', {
            'fields': ('jalur',),
            'description': 'Kosongkan untuk berlaku di semua jalur.',
        }),
        ('Audit', {
            'fields': ('dibuat_oleh', 'tgl_dibuat', 'tgl_diupdate'),
            'classes': ('collapse',),
        }),
    )
    date_hierarchy = 'tgl_dibuat'
    ordering = ('-tgl_dibuat',)

    def nilai_diskon_display(self, obj):
        if obj.jenis_diskon == 'persen':
            return f'{obj.nilai_diskon:.0f}%'
        return f'Rp {obj.nilai_diskon:,.0f}'.replace(',', '.')
    nilai_diskon_display.short_description = 'Nilai Diskon'

    def periode_display(self, obj):
        return f'{obj.berlaku_dari.strftime("%d %b %Y")} — {obj.berlaku_sampai.strftime("%d %b %Y")}'
    periode_display.short_description = 'Periode Berlaku'

    def kuota_display(self, obj):
        if obj.max_penggunaan == 0:
            return f'{obj.sudah_dipakai} / ∞'
        return f'{obj.sudah_dipakai} / {obj.max_penggunaan}'
    kuota_display.short_description = 'Pemakaian'

    def status_badge(self, obj):
        from django.utils.safestring import mark_safe
        if obj.status == 'nonaktif':
            return mark_safe('<span style="color:#888;">⊘ Nonaktif</span>')
        if obj.is_kadaluarsa:
            return mark_safe('<span style="color:#dc3545;">⏱ Kadaluarsa</span>')
        if obj.is_kuota_habis:
            return mark_safe('<span style="color:#fd7e14;">∅ Habis Kuota</span>')
        return mark_safe('<span style="color:#28a745;">✓ Aktif</span>')
    status_badge.short_description = 'Status Aktual'

    def save_model(self, request, obj, form, change):
        # Auto-set dibuat_oleh saat admin pertama kali save
        if not change and not obj.dibuat_oleh:
            obj.dibuat_oleh = request.user
        super().save_model(request, obj, form, change)