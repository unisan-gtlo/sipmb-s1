from django.contrib import admin
from .models import (
    BrosurFakultas, GaleriKampus, Pengumuman,
    FAQ, Testimoni, MitraKerjasama, MediaSosial, DokumenDownload
)


@admin.register(BrosurFakultas)
class BrosurFakultasAdmin(admin.ModelAdmin):
    list_display  = ['nama_fakultas', 'judul', 'urutan', 'status', 'tgl_upload']
    list_filter   = ['status', 'kode_fakultas']
    search_fields = ['nama_fakultas', 'judul']
    ordering      = ['urutan']


@admin.register(GaleriKampus)
class GaleriKampusAdmin(admin.ModelAdmin):
    list_display  = ['judul', 'kategori', 'urutan', 'status']
    list_filter   = ['status', 'kategori']
    search_fields = ['judul']
    ordering      = ['urutan']


@admin.register(Pengumuman)
class PengumumanAdmin(admin.ModelAdmin):
    list_display  = ['judul', 'tgl_tayang', 'tgl_selesai', 'penting', 'status']
    list_filter   = ['status', 'penting']
    search_fields = ['judul']
    ordering      = ['-penting', '-tgl_tayang']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display  = ['pertanyaan', 'kategori', 'urutan', 'status']
    list_filter   = ['status', 'kategori']
    search_fields = ['pertanyaan', 'jawaban']
    ordering      = ['kategori', 'urutan']


@admin.register(Testimoni)
class TestimoniAdmin(admin.ModelAdmin):
    list_display  = ['nama', 'prodi', 'angkatan', 'urutan', 'status']
    list_filter   = ['status']
    search_fields = ['nama', 'prodi']
    ordering      = ['urutan']


@admin.register(MitraKerjasama)
class MitraKerjasamaAdmin(admin.ModelAdmin):
    list_display  = ['nama_mitra', 'website', 'urutan', 'status']
    list_filter   = ['status']
    search_fields = ['nama_mitra']
    ordering      = ['urutan']


@admin.register(MediaSosial)
class MediaSosialAdmin(admin.ModelAdmin):
    list_display  = ['platform', 'nama_akun', 'url', 'urutan', 'status']
    list_filter   = ['status', 'platform']
    ordering      = ['urutan']


@admin.register(DokumenDownload)
class DokumenDownloadAdmin(admin.ModelAdmin):
    list_display  = ['judul', 'ukuran', 'urutan', 'status', 'tgl_upload']
    list_filter   = ['status']
    search_fields = ['judul']
    ordering      = ['urutan']