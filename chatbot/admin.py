from django.contrib import admin
from .models import KnowledgeBase, PengaturanChatbot, SesiChat, RiwayatChat


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display  = ['kategori', 'pertanyaan', 'urutan_prioritas', 'status', 'tgl_update']
    list_filter   = ['kategori', 'status']
    search_fields = ['pertanyaan', 'kata_kunci', 'jawaban']
    ordering      = ['kategori', 'urutan_prioritas']


@admin.register(PengaturanChatbot)
class PengaturanChatbotAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Identitas Bot', {
            'fields': ('nama_bot', 'deskripsi_bot', 'foto_bot', 'aktif')
        }),
        ('Pesan', {
            'fields': ('pesan_sambutan', 'pesan_fallback', 'pesan_eskalasi')
        }),
        ('AI Configuration', {
            'fields': ('ai_provider', 'ai_model', 'system_prompt', 'max_token'),
            'classes': ('collapse',)
        }),
        ('Jam Operasional', {
            'fields': ('jam_operasional', 'jam_buka', 'jam_tutup', 'pesan_diluar_jam')
        }),
    )

    def has_add_permission(self, request):
        return not PengaturanChatbot.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class RiwayatInline(admin.TabularInline):
    model      = RiwayatChat
    extra      = 0
    readonly_fields = ['pengirim', 'pesan', 'sumber_jawaban', 'tgl_kirim']
    can_delete = False


@admin.register(SesiChat)
class SesiChatAdmin(admin.ModelAdmin):
    list_display  = ['session_id', 'user', 'nama_tamu', 'total_pesan', 'status', 'tgl_mulai']
    list_filter   = ['status', 'eskalasi_ke_manusia']
    readonly_fields = ['session_id', 'tgl_mulai', 'tgl_terakhir']
    inlines       = [RiwayatInline]