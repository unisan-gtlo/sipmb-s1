# pembayaran/apps.py
from django.apps import AppConfig


class PembayaranConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pembayaran'
    verbose_name = 'Pembayaran'

    def ready(self):
        # Register signals — WAJIB agar auto-create Tagihan saat Pendaftaran dibuat
        import pembayaran.signals  # noqa: F401