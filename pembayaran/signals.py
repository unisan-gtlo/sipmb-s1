# pembayaran/signals.py
from decimal import Decimal

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='pendaftaran.Pendaftaran')
def create_tagihan_on_pendaftaran(sender, instance, created, **kwargs):
    """
    Auto-generate Tagihan 'biaya_pendaftaran' saat Pendaftaran baru dibuat.

    - Jumlah diambil dari gelombang.biaya_akhir (fallback: biaya_penuh).
    - Kalau gelombangnya gratis (biaya = 0), Tagihan langsung status='lunas'.
    - Idempoten: tidak membuat duplikat kalau sudah ada tagihan biaya_pendaftaran.
    """
    if not created:
        return

    Tagihan = apps.get_model('pembayaran', 'Tagihan')

    # Guard: jangan duplikat
    if Tagihan.objects.filter(
        pendaftaran=instance,
        jenis='biaya_pendaftaran',
    ).exists():
        return

    gelombang = getattr(instance, 'gelombang', None)
    if not gelombang:
        # Defensive — skip kalau Pendaftaran belum ter-assign gelombang
        return

    jumlah = (
        gelombang.biaya_akhir
        or gelombang.biaya_penuh
        or Decimal('0')
    )

    if jumlah == 0:
        status = 'lunas'
        catatan = 'Gelombang gratis — auto-lunas.'
    else:
        status = 'belum_bayar'
        catatan = 'Tagihan otomatis dibuat saat registrasi.'

    Tagihan.objects.create(
        pendaftaran=instance,
        jenis='biaya_pendaftaran',
        jumlah=jumlah,
        status=status,
        catatan=catatan,
    )