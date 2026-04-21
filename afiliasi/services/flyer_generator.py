"""
Flyer Generator Service untuk Recruiter SIPMB UNISAN.

Generate 4 template flyer (story, feed, cetak, banner) yang ter-personalisasi
dengan nama recruiter, kode referral, dan QR code menuju link referral unik.
"""

import io
import os
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.cache import cache


# ============================================================
# KONSTANTA
# ============================================================

FONT_DIR = Path(settings.BASE_DIR) / 'static' / 'fonts'

FONT_REGULAR  = str(FONT_DIR / 'Inter-Regular.ttf')
FONT_MEDIUM   = str(FONT_DIR / 'Inter-Medium.ttf')
FONT_SEMIBOLD = str(FONT_DIR / 'Inter-SemiBold.ttf')
FONT_BOLD     = str(FONT_DIR / 'Inter-Bold.ttf')

CACHE_TIMEOUT = 60 * 60 * 24  # 24 jam

BASE_URL = ''


# ============================================================
# CLASS FLYER GENERATOR
# ============================================================

class FlyerGenerator:
    """Generate flyer promosi PMB per recruiter.

    Usage:
        gen = FlyerGenerator(recruiter)
        png_bytes = gen.get_png_bytes('story')
    """

    def __init__(self, recruiter, konten=None, base_url=None):
        from afiliasi.models import KontenFlyer

        self.recruiter = recruiter
        self.konten = konten or KontenFlyer.get_aktif()
        self.base_url = (base_url or 'https://pmb.unisan.ac.id').rstrip('/')

        self.warna_primer   = self._hex_to_rgb(self.konten.warna_primer)
        self.warna_sekunder = self._hex_to_rgb(self.konten.warna_sekunder)
        self.warna_aksen    = self._hex_to_rgb(self.konten.warna_aksen)

    # ---------- HELPERS ----------

    @staticmethod
    def _hex_to_rgb(hex_color):
        """Convert '#RRGGBB' ke tuple (R, G, B)."""
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    @property
    def nama_recruiter(self):
        """Nama lengkap recruiter dari User model."""
        full_name = self.recruiter.user.get_full_name()
        if not full_name.strip():
            full_name = self.recruiter.user.username
        return full_name.strip()

    @property
    def link_referral(self):
        """URL lengkap link referral recruiter."""
        return f"{self.base_url}/accounts/daftar/?ref={self.recruiter.kode_referral}"

    def _font(self, style, size):
        """Load font TTF dengan fallback ke default bitmap font."""
        paths = {
            'regular':  FONT_REGULAR,
            'medium':   FONT_MEDIUM,
            'semibold': FONT_SEMIBOLD,
            'bold':     FONT_BOLD,
        }
        try:
            return ImageFont.truetype(paths.get(style, FONT_REGULAR), size)
        except (OSError, KeyError):
            return ImageFont.load_default()

    def _generate_qr(self, size_px):
        """Generate QR code PIL Image untuk link referral."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(self.link_referral)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white').convert('RGBA')
        return img.resize((size_px, size_px), Image.Resampling.LANCZOS)

    def _wrap_text(self, text, font, max_width, draw):
        """Wrap teks jadi multi-line sesuai lebar maksimal."""
        words = text.split()
        lines = []
        current = []
        for word in words:
            test = ' '.join(current + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(' '.join(current))
                current = [word]
        if current:
            lines.append(' '.join(current))
        return lines

    def _gradient_background(self, width, height):
        """Generate gradient diagonal ungu primer -> sekunder."""
        img = Image.new('RGBA', (width, height), self.warna_primer + (255,))
        draw = ImageDraw.Draw(img)

        c1 = self.warna_primer
        c2 = self.warna_sekunder
        steps = max(width, height)

        for i in range(steps):
            ratio = i / steps
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            draw.line([(0, i), (i, 0)], fill=(r, g, b, 255), width=2)

        return img

    def _overlay_foto_kampus(self, bg, opacity=0.08):
        """Overlay banner_utama dari PengaturanSistem dengan opacity rendah.

        Jika banner tidak ada atau error, return bg tanpa perubahan.
        """
        try:
            from master.models import PengaturanSistem
            pengaturan = PengaturanSistem.objects.first()
            if not pengaturan or not pengaturan.banner_utama:
                return bg

            foto_path = pengaturan.banner_utama.path
            if not os.path.exists(foto_path):
                return bg

            foto = Image.open(foto_path).convert('RGBA')

            # Resize foto menutupi bg dengan cover
            bg_ratio = bg.size[0] / bg.size[1]
            foto_ratio = foto.size[0] / foto.size[1]

            if foto_ratio > bg_ratio:
                new_h = bg.size[1]
                new_w = int(new_h * foto_ratio)
            else:
                new_w = bg.size[0]
                new_h = int(new_w / foto_ratio)

            foto = foto.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Crop center
            left = (new_w - bg.size[0]) // 2
            top  = (new_h - bg.size[1]) // 2
            foto = foto.crop((left, top, left + bg.size[0], top + bg.size[1]))

            # Turunkan opacity
            alpha = foto.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            foto.putalpha(alpha)

            bg.paste(foto, (0, 0), foto)
        except Exception as e:
            # Diam-diam fallback ke gradient kalau foto gagal
            pass

        return bg

    def _draw_logo_header(self, draw, img, x, y, big=False):
        """Gambar logo UNISAN + nama kampus di header."""
        size_logo = 96 if big else 72
        size_nama = 40 if big else 32
        size_sub  = 22 if big else 18

        # Lingkaran putih sebagai background logo
        draw.ellipse(
            [(x, y), (x + size_logo, y + size_logo)],
            fill=(255, 255, 255, 255)
        )

        # Coba load logo UNISAN real
        logo_loaded = False
        try:
            from master.models import PengaturanSistem
            pengaturan = PengaturanSistem.objects.first()
            if pengaturan and pengaturan.logo and os.path.exists(pengaturan.logo.path):
                logo_img = Image.open(pengaturan.logo.path).convert('RGBA')
                padding = 8
                target = size_logo - (padding * 2)
                logo_img = logo_img.resize((target, target), Image.Resampling.LANCZOS)
                img.paste(logo_img, (x + padding, y + padding), logo_img)
                logo_loaded = True
        except Exception:
            pass

        if not logo_loaded:
            # Fallback: huruf "U" ungu di tengah lingkaran
            font_u = self._font('bold', size_logo - 24)
            bbox = draw.textbbox((0, 0), 'U', font=font_u)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                (x + (size_logo - tw) // 2, y + (size_logo - th) // 2 - 6),
                'U', font=font_u, fill=self.warna_primer
            )

        # Teks nama kampus sebelah kanan logo
        font_nama = self._font('semibold', size_nama)
        draw.text(
            (x + size_logo + 20, y + 6),
            'UNISAN',
            font=font_nama, fill=(255, 255, 255, 255)
        )

        font_sub = self._font('regular', size_sub)
        draw.text(
            (x + size_logo + 20, y + size_nama + 14),
            'Universitas Ichsan Gorontalo',
            font=font_sub, fill=(255, 255, 255, 220)
        )

    def _draw_footer_card(self, img, W, H, y_top, mode='story'):
        """Gambar card QR + info recruiter di footer.

        mode: 'story' / 'feed' (translucent white card on dark bg)
              'cetak' (solid card on white bg)
        """
        if mode == 'cetak':
            self._draw_footer_card_cetak(img, W, H, y_top)
            return

        qr_size = 200 if mode == 'story' else 180
        card_h = qr_size + 50

        # Card background (translucent white)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        draw_ov.rounded_rectangle(
            [(60, y_top), (W - 60, y_top + card_h)],
            radius=24,
            fill=(255, 255, 255, 45)
        )
        img.alpha_composite(overlay)

        draw = ImageDraw.Draw(img)

        # QR code
        qr_img = self._generate_qr(qr_size)
        qr_x = 90
        qr_y = y_top + 25
        img.paste(qr_img, (qr_x, qr_y), qr_img)

        # Info di sebelah kanan QR
        text_x = qr_x + qr_size + 30

        font_label = self._font('regular', 24)
        draw.text(
            (text_x, qr_y + 8),
            'Daftar via Recruiter',
            font=font_label, fill=(255, 255, 255, 210)
        )

        font_nama = self._font('semibold', 34)
        nama_truncated = self.nama_recruiter[:26]
        draw.text(
            (text_x, qr_y + 44),
            nama_truncated,
            font=font_nama, fill=(255, 255, 255, 255)
        )

        font_kode = self._font('medium', 26)
        draw.text(
            (text_x, qr_y + 96),
            f'Kode: {self.recruiter.kode_referral}',
            font=font_kode, fill=(255, 255, 255, 230)
        )

        font_web = self._font('regular', 22)
        draw.text(
            (text_x, qr_y + 134),
            self.konten.website_display,
            font=font_web, fill=(255, 255, 255, 200)
        )

    def _draw_footer_card_cetak(self, img, W, H, y_top):
        """Footer card khusus mode cetak (white bg, dark text)."""
        draw = ImageDraw.Draw(img)

        qr_size = 220
        qr_img = self._generate_qr(qr_size)
        qr_x = 60
        qr_y = y_top
        img.paste(qr_img, (qr_x, qr_y), qr_img)

        text_x = qr_x + qr_size + 40

        font_label = self._font('regular', 22)
        draw.text(
            (text_x, qr_y + 10),
            'SCAN untuk daftar',
            font=font_label, fill=(130, 130, 130, 255)
        )

        font_nama = self._font('semibold', 36)
        draw.text(
            (text_x, qr_y + 48),
            self.nama_recruiter[:24],
            font=font_nama, fill=self.warna_primer + (255,)
        )

        font_kode = self._font('medium', 24)
        draw.text(
            (text_x, qr_y + 108),
            f'Kode: {self.recruiter.kode_referral}',
            font=font_kode, fill=self.warna_sekunder + (255,)
        )

        font_web = self._font('regular', 22)
        draw.text(
            (text_x, qr_y + 148),
            self.konten.website_display,
            font=font_web, fill=(130, 130, 130, 255)
        )
        # Info kontak PMB di bawah QR (jika nomor WA diisi admin)
        if self.konten.nomor_wa_pmb:
            info_y = qr_y + qr_size + 30

            # Garis pemisah tipis
            draw.line(
                [(60, info_y), (W - 60, info_y)],
                fill=(230, 230, 230, 255), width=1
            )

            info_y += 20

            # Icon WA (lingkaran hijau WhatsApp)
            icon_size = 32
            draw.ellipse(
                [(60, info_y), (60 + icon_size, info_y + icon_size)],
                fill=(37, 211, 102, 255)
            )
            # Huruf W di tengah icon
            font_icon = self._font('bold', 18)
            draw.text(
                (60 + 9, info_y + 5),
                'W', font=font_icon, fill=(255, 255, 255, 255)
            )

            # Label + nomor
            font_info_lbl = self._font('regular', 20)
            draw.text(
                (60 + icon_size + 14, info_y - 2),
                'Info & Pendaftaran PMB:',
                font=font_info_lbl, fill=(130, 130, 130, 255)
            )

            font_info_wa = self._font('semibold', 24)
            draw.text(
                (60 + icon_size + 14, info_y + 20),
                self.konten.nomor_wa_pmb,
                font=font_info_wa, fill=(60, 60, 60, 255)
            )
    # ---------- RENDER TEMPLATES ----------

    def render_story(self):
        """Template 1: Story 1080x1920 untuk IG Story / WA Status."""
        W, H = 1080, 1920

        img = self._gradient_background(W, H)
        img = self._overlay_foto_kampus(img, opacity=0.08)

        # Dark overlay di area bawah agar teks terbaca
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        draw_ov.rectangle([(0, 820), (W, H)], fill=(0, 0, 0, 110))
        img.alpha_composite(overlay)

        draw = ImageDraw.Draw(img)

        # Dekorasi lingkaran
        deco = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_deco = ImageDraw.Draw(deco)
        draw_deco.ellipse([(W - 300, -200), (W + 100, 200)], fill=(255, 255, 255, 22))
        draw_deco.ellipse([(-200, H - 400), (300, H + 100)], fill=(255, 255, 255, 15))
        img.alpha_composite(deco)

        draw = ImageDraw.Draw(img)

        # Header: Logo + nama kampus
        self._draw_logo_header(draw, img, 80, 90, big=True)

        # Label PMB
        font_label = self._font('medium', 30)
        draw.text(
            (80, 720),
            f'PMB {self.konten.tahun_akademik}',
            font=font_label, fill=(255, 255, 255, 230)
        )

        # Headline utama
        font_headline = self._font('bold', 84)
        lines = self._wrap_text(self.konten.headline_utama, font_headline, W - 160, draw)
        y = 790
        for line in lines:
            draw.text((80, y), line, font=font_headline, fill=(255, 255, 255, 255))
            y += 98

        # Sub-headline
        font_sub = self._font('regular', 34)
        sub_lines = self._wrap_text(self.konten.sub_headline, font_sub, W - 160, draw)
        y += 30
        for line in sub_lines:
            draw.text((80, y), line, font=font_sub, fill=(255, 255, 255, 230))
            y += 48

        # Footer card dengan QR
        self._draw_footer_card(img, W, H, y_top=H - 380, mode='story')

        return img

    def render_feed(self):
        """Template 2: Feed 1080x1080 untuk IG Feed / FB Post."""
        W, H = 1080, 1080

        img = self._gradient_background(W, H)
        img = self._overlay_foto_kampus(img, opacity=0.08)

        # Dekorasi
        deco = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_deco = ImageDraw.Draw(deco)
        draw_deco.ellipse(
            [(W - 250, H // 2 - 100), (W + 200, H // 2 + 350)],
            fill=(255, 255, 255, 20)
        )
        img.alpha_composite(deco)

        draw = ImageDraw.Draw(img)

        # Header
        self._draw_logo_header(draw, img, 60, 60)

        # Badge PMB kanan atas
        badge_text = f'PMB {self.konten.tahun_akademik}'
        font_badge = self._font('medium', 24)
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        badge_w = bbox[2] - bbox[0] + 44
        draw.rounded_rectangle(
            [(W - badge_w - 60, 70), (W - 60, 120)],
            radius=25,
            fill=(255, 255, 255, 50)
        )
        draw.text(
            (W - badge_w - 38, 84),
            badge_text, font=font_badge, fill=(255, 255, 255, 255)
        )

        # Headline
        font_headline = self._font('bold', 68)
        lines = self._wrap_text(self.konten.headline_utama, font_headline, W - 120, draw)
        total_h = len(lines) * 80
        y = (H - total_h) // 2 - 80
        for line in lines:
            draw.text((60, y), line, font=font_headline, fill=(255, 255, 255, 255))
            y += 80

        # Fitur list
        font_fitur = self._font('medium', 26)
        fitur_text = (
            f'  {self.konten.jumlah_fakultas} Fakultas     '
            f'  {self.konten.jumlah_prodi} Prodi     '
            f'  Terakreditasi BAN-PT'
        )
        draw.text((60, y + 20), fitur_text, font=font_fitur, fill=(255, 255, 255, 230))

        # Footer card
        self._draw_footer_card(img, W, H, y_top=H - 240, mode='feed')

        return img

    def render_cetak(self):
        """Template 3: Flyer cetak 1200x1800 (2:3) untuk print A5/A4."""
        W, H = 1200, 1800

        img = Image.new('RGBA', (W, H), (255, 255, 255, 255))

        # Header strip gradient
        HEADER_H = 320
        header = self._gradient_background(W, HEADER_H)
        img.paste(header, (0, 0))

        draw = ImageDraw.Draw(img)

        # Logo + nama kampus di header
        self._draw_logo_header(draw, img, 60, 90, big=True)

        # Label PMB
        font_label = self._font('medium', 28)
        draw.text(
            (60, 240),
            f'PENERIMAAN MAHASISWA BARU {self.konten.tahun_akademik}',
            font=font_label, fill=(255, 255, 255, 240)
        )

        # ==== BODY ====
        y = HEADER_H + 80

        # Headline
        font_headline = self._font('bold', 62)
        lines = self._wrap_text(self.konten.headline_utama, font_headline, W - 120, draw)
        for line in lines:
            draw.text((60, y), line, font=font_headline, fill=self.warna_primer + (255,))
            y += 76

        y += 40

        # Stat cards
        stat_y = y
        card_w = (W - 120 - 40) // 2
        card_h = 180

        # Card 1: Fakultas
        draw.rounded_rectangle(
            [(60, stat_y), (60 + card_w, stat_y + card_h)],
            radius=14,
            fill=(238, 237, 254, 255)
        )
        font_stat = self._font('bold', 88)
        draw.text(
            (60 + 50, stat_y + 20),
            str(self.konten.jumlah_fakultas),
            font=font_stat, fill=self.warna_primer + (255,)
        )
        font_stat_lbl = self._font('medium', 26)
        draw.text(
            (60 + 50, stat_y + 130),
            'Fakultas',
            font=font_stat_lbl, fill=self.warna_sekunder + (255,)
        )

        # Card 2: Prodi
        x2 = 60 + card_w + 40
        draw.rounded_rectangle(
            [(x2, stat_y), (x2 + card_w, stat_y + card_h)],
            radius=14,
            fill=(238, 237, 254, 255)
        )
        draw.text(
            (x2 + 50, stat_y + 20),
            str(self.konten.jumlah_prodi),
            font=font_stat, fill=self.warna_primer + (255,)
        )
        draw.text(
            (x2 + 50, stat_y + 130),
            'Program Studi',
            font=font_stat_lbl, fill=self.warna_sekunder + (255,)
        )

        y = stat_y + card_h + 40

        # Jalur penerimaan
        font_jalur_lbl = self._font('semibold', 28)
        draw.text(
            (60, y),
            'Jalur Penerimaan:',
            font=font_jalur_lbl, fill=self.warna_primer + (255,)
        )
        y += 50
        font_jalur = self._font('regular', 28)
        draw.text(
            (60, y),
            self.konten.jalur_tersedia,
            font=font_jalur, fill=(80, 80, 80, 255)
        )

        # Garis putus-putus
        y += 90
        for i in range(60, W - 60, 24):
            draw.line([(i, y), (i + 12, y)], fill=(206, 203, 246, 255), width=2)

        y += 60

        # Footer card
        self._draw_footer_card(img, W, H, y_top=y, mode='cetak')

        return img

    def render_banner(self):
        """Template 4: Banner landscape 1920x1080 (16:9)."""
        W, H = 1920, 1080

        img = self._gradient_background(W, H)
        img = self._overlay_foto_kampus(img, opacity=0.08)

        # Dekorasi
        deco = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_deco = ImageDraw.Draw(deco)
        draw_deco.ellipse(
            [(W // 2, H - 200), (W // 2 + 400, H + 200)],
            fill=(255, 255, 255, 20)
        )
        draw_deco.ellipse(
            [(W // 3, -100), (W // 3 + 300, 200)],
            fill=(255, 255, 255, 15)
        )
        img.alpha_composite(deco)

        draw = ImageDraw.Draw(img)

        # Header kiri
        self._draw_logo_header(draw, img, 80, 80, big=True)

        # Label PMB
        font_label = self._font('medium', 30)
        draw.text(
            (80, H // 2 - 160),
            f'PMB {self.konten.tahun_akademik}',
            font=font_label, fill=(255, 255, 255, 220)
        )

        # Headline
        LEFT_W = W - 500
        font_headline = self._font('bold', 76)
        lines = self._wrap_text(self.konten.headline_utama, font_headline, LEFT_W - 120, draw)
        y = H // 2 - 100
        for line in lines:
            draw.text((80, y), line, font=font_headline, fill=(255, 255, 255, 255))
            y += 90

        # Sub-headline
        font_sub = self._font('regular', 30)
        draw.text(
            (80, y + 30),
            self.konten.sub_headline,
            font=font_sub, fill=(255, 255, 255, 230)
        )

        # Info recruiter di kiri bawah
        font_rec = self._font('medium', 26)
        rec_text = f'{self.nama_recruiter}  -  {self.recruiter.kode_referral}'
        draw.text(
            (80, H - 100),
            rec_text[:60],
            font=font_rec, fill=(255, 255, 255, 230)
        )

        # QR code besar di kanan
        qr_size = 320
        qr_img = self._generate_qr(qr_size)
        qr_x = W - qr_size - 100
        qr_y = (H - qr_size) // 2 - 40

        # Background putih untuk QR
        draw.rounded_rectangle(
            [(qr_x - 24, qr_y - 24), (qr_x + qr_size + 24, qr_y + qr_size + 80)],
            radius=18,
            fill=(255, 255, 255, 255)
        )
        img.paste(qr_img, (qr_x, qr_y), qr_img)

        # Label scan
        font_scan = self._font('medium', 24)
        scan_text = 'Scan untuk daftar'
        bbox = draw.textbbox((0, 0), scan_text, font=font_scan)
        tw = bbox[2] - bbox[0]
        draw.text(
            (qr_x + (qr_size - tw) // 2, qr_y + qr_size + 25),
            scan_text,
            font=font_scan, fill=(70, 70, 70, 255)
        )

        return img

    # ---------- PUBLIC API ----------

    def render(self, kode_template):
        """Dispatcher render sesuai kode template."""
        methods = {
            'story':  self.render_story,
            'feed':   self.render_feed,
            'cetak':  self.render_cetak,
            'banner': self.render_banner,
        }
        method = methods.get(kode_template)
        if not method:
            raise ValueError(f"Template '{kode_template}' tidak dikenal.")
        return method()

    def get_png_bytes(self, kode_template):
        """Return PNG bytes — cached 24 jam per (recruiter, template, konten)."""
        cache_key = (
            f'flyer:png:{self.recruiter.id}:{kode_template}:'
            f'{self.konten.id}:{hash(self.base_url)}'
        )
        cached = cache.get(cache_key)
        if cached:
            return cached

        img = self.render(kode_template)
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, format='PNG', optimize=True)
        png_bytes = buffer.getvalue()

        cache.set(cache_key, png_bytes, CACHE_TIMEOUT)
        return png_bytes

    def get_pdf_bytes(self, kode_template='cetak'):
        """Return PDF bytes A5 untuk cetak."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A5
        from reportlab.lib.utils import ImageReader

        cache_key = (
            f'flyer:pdf:{self.recruiter.id}:{kode_template}:'
            f'{self.konten.id}:{hash(self.base_url)}'
        )
        cached = cache.get(cache_key)
        if cached:
            return cached

        img = self.render(kode_template)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A5)
        page_w, page_h = A5

        img_reader = ImageReader(img.convert('RGB'))
        c.drawImage(
            img_reader, 0, 0,
            width=page_w, height=page_h,
            preserveAspectRatio=True, anchor='c'
        )
        c.save()

        pdf_bytes = buffer.getvalue()
        cache.set(cache_key, pdf_bytes, CACHE_TIMEOUT)
        return pdf_bytes