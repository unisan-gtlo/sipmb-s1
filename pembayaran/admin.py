# pembayaran/admin.py
from django.contrib import admin
from .models import RekeningTujuan, Tagihan, KonfirmasiPembayaran


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