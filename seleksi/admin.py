from django.contrib import admin
from .models import JadwalSeleksi, PesertaSeleksi, HasilPenerimaan, KartuPeserta


class PesertaInline(admin.TabularInline):
    model       = PesertaSeleksi
    extra       = 0
    fields      = ['pendaftaran', 'no_ujian', 'status_kehadiran', 'nilai']


@admin.register(JadwalSeleksi)
class JadwalSeleksiAdmin(admin.ModelAdmin):
    list_display  = ['nama_seleksi', 'jalur', 'gelombang', 'jenis_seleksi',
                     'tgl_seleksi', 'jam_mulai', 'status']
    list_filter   = ['jenis_seleksi', 'status', 'jalur', 'gelombang']
    search_fields = ['nama_seleksi', 'lokasi']
    inlines       = [PesertaInline]


@admin.register(HasilPenerimaan)
class HasilPenerimaanAdmin(admin.ModelAdmin):
    list_display  = ['pendaftaran', 'prodi_diterima', 'status',
                     'nilai_akhir', 'peringkat', 'tgl_pengumuman']
    list_filter   = ['status', 'prodi_diterima']
    search_fields = ['pendaftaran__no_pendaftaran',
                     'pendaftaran__user__first_name']


@admin.register(KartuPeserta)
class KartuPesertaAdmin(admin.ModelAdmin):
    list_display  = ['no_kartu', 'pendaftaran', 'sudah_cetak', 'tgl_cetak']
    list_filter   = ['sudah_cetak']