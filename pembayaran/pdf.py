# pembayaran/pdf.py
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# ==================== TERBILANG ====================
def _terbilang(n):
    n = int(n)
    angka = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh",
             "delapan", "sembilan", "sepuluh", "sebelas"]
    if n == 0:
        return "nol"
    if n < 12:
        return angka[n]
    if n < 20:
        return _terbilang(n - 10) + " belas"
    if n < 100:
        sisa = n % 10
        return _terbilang(n // 10) + " puluh" + (" " + _terbilang(sisa) if sisa else "")
    if n < 200:
        sisa = n - 100
        return "seratus" + (" " + _terbilang(sisa) if sisa else "")
    if n < 1000:
        sisa = n % 100
        return _terbilang(n // 100) + " ratus" + (" " + _terbilang(sisa) if sisa else "")
    if n < 2000:
        sisa = n - 1000
        return "seribu" + (" " + _terbilang(sisa) if sisa else "")
    if n < 1_000_000:
        sisa = n % 1000
        return _terbilang(n // 1000) + " ribu" + (" " + _terbilang(sisa) if sisa else "")
    if n < 1_000_000_000:
        sisa = n % 1_000_000
        return _terbilang(n // 1_000_000) + " juta" + (" " + _terbilang(sisa) if sisa else "")
    if n < 1_000_000_000_000:
        sisa = n % 1_000_000_000
        return _terbilang(n // 1_000_000_000) + " miliar" + (" " + _terbilang(sisa) if sisa else "")
    return "nilai terlalu besar"


def terbilang(n):
    """Format: 'Seratus lima puluh ribu rupiah'"""
    s = _terbilang(n).strip()
    while "  " in s:
        s = s.replace("  ", " ")
    return s.capitalize() + " rupiah"


# ==================== DATE FORMAT ID ====================
_BULAN_ID = {
    "January": "Januari", "February": "Februari", "March": "Maret",
    "April": "April", "May": "Mei", "June": "Juni",
    "July": "Juli", "August": "Agustus", "September": "September",
    "October": "Oktober", "November": "November", "December": "Desember",
}

def format_tgl_id(dt):
    s = dt.strftime("%d %B %Y")
    for en, id_ in _BULAN_ID.items():
        s = s.replace(en, id_)
    return s


# ==================== KWITANSI GENERATOR ====================
def generate_kwitansi_pdf(konfirmasi):
    """Generate PDF kwitansi dari KonfirmasiPembayaran status='dikonfirmasi'."""
    tagihan = konfirmasi.tagihan
    pendaftaran = tagihan.pendaftaran

    # Ambil data institusi (fallback default kalau SIMDA tidak accessible)
    try:
        from utils.simda_reader import get_institusi
        institusi = get_institusi() or {}
    except Exception:
        institusi = {}

    nama_institusi = institusi.get('nama', 'UNIVERSITAS ICHSAN GORONTALO')
    alamat_institusi = institusi.get('alamat', 'Jl. Achmad Nadjamuddin No. 17, Kota Gorontalo')
    telepon = institusi.get('telepon') or institusi.get('no_telepon') or '-'
    email = institusi.get('email') or '-'

    logo_path = Path(settings.BASE_DIR) / 'static' / 'assets' / 'logo_unisan.png'

    buffer = BytesIO()
    page = landscape(A5)   # 210 x 148 mm
    c = canvas.Canvas(buffer, pagesize=page)
    W, H = page

    # ========== HEADER ==========
    if logo_path.exists():
        try:
            c.drawImage(
                ImageReader(str(logo_path)),
                10 * mm, H - 28 * mm,
                width=20 * mm, height=20 * mm,
                preserveAspectRatio=True, mask='auto',
            )
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, H - 12 * mm, nama_institusi.upper())
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, H - 17 * mm, alamat_institusi)
    c.drawCentredString(W / 2, H - 21 * mm, f"Telp: {telepon}  |  Email: {email}")

    # Double line
    c.setLineWidth(1.5)
    c.line(10 * mm, H - 30 * mm, W - 10 * mm, H - 30 * mm)
    c.setLineWidth(0.5)
    c.line(10 * mm, H - 31.5 * mm, W - 10 * mm, H - 31.5 * mm)

    # ========== TITLE ==========
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 41 * mm, "KWITANSI PEMBAYARAN")

    tgl_konfirmasi = konfirmasi.tgl_konfirmasi or timezone.now()
    no_kwitansi = f"KW/{konfirmasi.id:05d}/PMB/{tgl_konfirmasi.year}"
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, H - 46 * mm, f"Nomor: {no_kwitansi}")

    # ========== BODY ==========
    y = H - 58 * mm
    line_h = 6 * mm
    col_label = 15 * mm
    col_colon = 55 * mm
    col_value = 58 * mm

    def row(label, value, bold=False):
        nonlocal y
        c.setFont("Helvetica", 10)
        c.drawString(col_label, y, label)
        c.drawString(col_colon, y, ":")
        if bold:
            c.setFont("Helvetica-Bold", 10)
        c.drawString(col_value, y, str(value))
        y -= line_h

    nama_pendaftar = (
        getattr(pendaftaran, 'nama_lengkap', None)
        or pendaftaran.user.get_full_name()
        or pendaftaran.user.email
    )
    jumlah_fmt = f"Rp {tagihan.jumlah:,.0f}".replace(",", ".")

    row("Telah diterima dari", nama_pendaftar, bold=True)
    row("No. Pendaftaran", pendaftaran.no_pendaftaran)
    row("Uang sebesar", jumlah_fmt, bold=True)
    row("Terbilang", f"# {terbilang(tagihan.jumlah)} #")
    row("Untuk pembayaran", tagihan.get_jenis_display())
    row("Kode Bayar", tagihan.kode_bayar)
    row("Metode", konfirmasi.get_metode_bayar_display())
    if konfirmasi.rekening_tujuan:
        row("Rekening Tujuan", f"{konfirmasi.rekening_tujuan.nama_bank} — {konfirmasi.rekening_tujuan.no_rekening}")

    # ========== TTD AREA ==========
    ttd_x = W - 80 * mm
    ttd_top = 42 * mm

    c.setFont("Helvetica", 9)
    c.drawString(ttd_x, ttd_top, f"Gorontalo, {format_tgl_id(tgl_konfirmasi)}")
    c.drawString(ttd_x, ttd_top - 4 * mm, "Panitia PMB UNISAN")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(ttd_x, ttd_top - 22 * mm, "______________________")

    c.setFont("Helvetica", 9)
    admin_name = (
        konfirmasi.dikonfirmasi_oleh.get_full_name()
        if konfirmasi.dikonfirmasi_oleh else "Panitia PMB"
    )
    c.drawString(ttd_x, ttd_top - 26 * mm, f"({admin_name})")

    # ========== FOOTER ==========
    c.setFont("Helvetica-Oblique", 7)
    c.setFillGray(0.4)
    c.drawCentredString(
        W / 2, 8 * mm,
        "Kwitansi ini sah dan diterbitkan otomatis oleh sistem SIPMB UNISAN. "
        "Dokumen digital, tidak memerlukan tanda tangan basah."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer