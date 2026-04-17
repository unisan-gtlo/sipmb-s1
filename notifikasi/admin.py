from django.contrib import admin
from .models import TemplateNotifikasi, LogNotifikasi


@admin.register(TemplateNotifikasi)
class TemplateNotifikasiAdmin(admin.ModelAdmin):
    list_display  = ['nama', 'trigger', 'jenis', 'aktif', 'tgl_update']
    list_filter   = ['jenis', 'aktif']
    search_fields = ['nama', 'subjek_email']
    list_editable = ['aktif']


@admin.register(LogNotifikasi)
class LogNotifikasiAdmin(admin.ModelAdmin):
    list_display  = ['tgl_kirim', 'user', 'jenis', 'tujuan', 'subjek', 'status']
    list_filter   = ['jenis', 'status']
    search_fields = ['tujuan', 'user__email']
    readonly_fields = ['tgl_kirim']