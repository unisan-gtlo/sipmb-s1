# pembayaran/utils.py
"""
Helper functions untuk modul pembayaran.

Berisi:
- validasi_voucher(kode, jalur) : validasi kode voucher saat input pendaftar
- hitung_potongan(voucher, biaya) : kalkulasi potongan dari voucher ke biaya
"""
from decimal import Decimal
from django.utils import timezone


def validasi_voucher(kode, jalur=None):
    """
    Validasi kode voucher untuk biaya pendaftaran.

    Args:
        kode (str): Kode voucher yang diinput user (case-insensitive)
        jalur (JalurPenerimaan, optional): Jalur pendaftaran user.
            Diperlukan untuk cek apakah voucher berlaku untuk jalur tsb.

    Returns:
        tuple (voucher, error_msg):
            - voucher (KodeVoucher | None): instance voucher jika valid, else None
            - error_msg (str | None): pesan error jika invalid, else None

    Contoh penggunaan:
        voucher, err = validasi_voucher('MERDEKA100', jalur=jalur_reguler)
        if err:
            raise ValidationError(err)
        # gunakan voucher untuk hitung potongan
    """
    # Import di dalam function untuk hindari circular import
    from pembayaran.models import KodeVoucher

    if not kode:
        # Kode kosong = tidak pakai voucher (bukan error, sah-sah saja)
        return None, None

    kode_clean = kode.strip().upper()

    # Cek voucher exist
    try:
        voucher = KodeVoucher.objects.get(kode_voucher=kode_clean)
    except KodeVoucher.DoesNotExist:
        return None, f"Kode voucher '{kode_clean}' tidak ditemukan."

    # Cek status aktif
    if voucher.status != 'aktif':
        return None, f"Kode voucher '{kode_clean}' sedang nonaktif."

    # Cek periode berlaku
    today = timezone.now().date()
    if today < voucher.berlaku_dari:
        return None, (
            f"Kode voucher '{kode_clean}' belum berlaku "
            f"(mulai {voucher.berlaku_dari.strftime('%d-%m-%Y')})."
        )
    if today > voucher.berlaku_sampai:
        return None, (
            f"Kode voucher '{kode_clean}' sudah kadaluarsa "
            f"(berakhir {voucher.berlaku_sampai.strftime('%d-%m-%Y')})."
        )

    # Cek kuota
    if voucher.is_kuota_habis:
        return None, f"Kode voucher '{kode_clean}' sudah habis kuotanya."

    # Cek jalur (kalau voucher di-restrict ke jalur tertentu)
    if voucher.jalur_id and jalur and voucher.jalur_id != jalur.pk:
        return None, (
            f"Kode voucher '{kode_clean}' tidak berlaku untuk "
            f"jalur {jalur.nama}. Hanya berlaku untuk jalur {voucher.jalur.nama}."
        )

    # Semua valid
    return voucher, None


def hitung_potongan(voucher, biaya):
    """
    Hitung nominal potongan dan biaya final dari voucher.

    Args:
        voucher (KodeVoucher): instance voucher yang sudah valid
        biaya (Decimal | int): biaya penuh sebelum potongan (rupiah)

    Returns:
        tuple (potongan, biaya_final):
            - potongan (Decimal): nominal potongan dalam rupiah
            - biaya_final (Decimal): biaya setelah potongan (minimal Rp 0)

    Contoh:
        # Voucher persen 100% atas biaya Rp 150.000
        potongan, final = hitung_potongan(voucher_merdeka, 150000)
        # potongan = 150000, final = 0

        # Voucher nominal Rp 50.000 atas biaya Rp 150.000
        potongan, final = hitung_potongan(voucher_potong50k, 150000)
        # potongan = 50000, final = 100000
    """
    biaya = Decimal(str(biaya))
    nilai = Decimal(str(voucher.nilai_diskon))

    if voucher.jenis_diskon == 'persen':
        # Cap persen di 100 untuk safety (kalau admin salah input >100)
        if nilai > Decimal('100'):
            nilai = Decimal('100')
        potongan = (biaya * nilai / Decimal('100')).quantize(Decimal('1'))
    else:
        # Nominal langsung
        potongan = nilai.quantize(Decimal('1'))

    # Biaya final tidak boleh negatif
    biaya_final = max(Decimal('0'), biaya - potongan)
    # Pastikan potongan tidak melebihi biaya (kalau nominal > biaya)
    potongan = min(potongan, biaya)

    return potongan, biaya_final

def apply_voucher_ke_tagihan(pendaftaran, voucher):
    """
    Apply voucher ke Tagihan biaya_pendaftaran milik Pendaftaran.
    Dipanggil dari view registrasi setelah Pendaftaran dibuat.

    Yang dilakukan:
    1. Cari Tagihan biaya_pendaftaran milik pendaftaran (yang baru dibuat oleh signal).
    2. Hitung potongan & biaya final.
    3. Update jumlah Tagihan & catatan.
    4. Kalau biaya final = Rp 0 → status Tagihan jadi 'lunas',
       status Pendaftaran jadi 'GRATIS_VOUCHER'.
    5. Increment counter sudah_dipakai voucher (atomic via F()).

    Args:
        pendaftaran (Pendaftaran): instance pendaftaran yang baru dibuat
        voucher (KodeVoucher): instance voucher yang sudah valid

    Returns:
        dict: {'tagihan': tagihan_obj, 'potongan': Decimal, 'biaya_final': Decimal}
              atau None kalau gagal (mis. tagihan tidak ditemukan).
    """
    from django.db.models import F
    from django.db import transaction
    from pembayaran.models import Tagihan, KodeVoucher

    with transaction.atomic():
        # Lock tagihan untuk update (hindari race condition)
        try:
            tagihan = Tagihan.objects.select_for_update().get(
                pendaftaran=pendaftaran,
                jenis='biaya_pendaftaran',
            )
        except Tagihan.DoesNotExist:
            return None

        biaya_awal = tagihan.jumlah
        potongan, biaya_final = hitung_potongan(voucher, biaya_awal)

        # Update tagihan
        tagihan.jumlah  = biaya_final
        tagihan.catatan = (
            f"Voucher {voucher.kode_voucher} diterapkan: "
            f"potongan Rp {potongan:,.0f} dari Rp {biaya_awal:,.0f}."
        ).replace(',', '.')

        if biaya_final == 0:
            tagihan.status = 'lunas'
            # Update status pendaftaran ke GRATIS_VOUCHER
            type(pendaftaran).objects.filter(pk=pendaftaran.pk).update(
                status='GRATIS_VOUCHER'
            )
            # Auto-create KonfirmasiPembayaran agar kwitansi bisa dicetak
            from pembayaran.models import KonfirmasiPembayaran
            from django.utils import timezone as dj_timezone
            now = dj_timezone.now()
            KonfirmasiPembayaran.objects.create(
                tagihan            = tagihan,
                metode_bayar       = 'voucher',
                jumlah_bayar       = 0,
                tgl_bayar          = now.date(),
                atas_nama_pengirim = f'Voucher {voucher.kode_voucher}',
                no_transaksi       = voucher.kode_voucher,
                status             = 'dikonfirmasi',
                tgl_konfirmasi     = now,
                catatan_pengirim   = (
                    f'Pembayaran lunas otomatis via voucher '
                    f'{voucher.kode_voucher} (potongan 100%).'
                ),
            )

        tagihan.save(update_fields=['jumlah', 'catatan', 'status'])

        # Increment counter pemakaian voucher (atomic)
        KodeVoucher.objects.filter(pk=voucher.pk).update(
            sudah_dipakai=F('sudah_dipakai') + 1
        )

    return {
        'tagihan':     tagihan,
        'potongan':    potongan,
        'biaya_final': biaya_final,
    }