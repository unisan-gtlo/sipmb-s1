import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from django.conf import settings

UNGU     = colors.HexColor('#667eea')
UNGU_TUA = colors.HexColor('#764ba2')
ABU      = colors.HexColor('#64748b')
ABU_MUDA = colors.HexColor('#f1f5f9')
HITAM    = colors.HexColor('#1e1e2e')


def buat_kartu_peserta(pendaftaran, jadwal=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    lebar, tinggi = A4

    # ===== HEADER BACKGROUND =====
    c.setFillColor(UNGU)
    c.rect(0, tinggi - 4.5*cm, lebar, 4.5*cm, fill=1, stroke=0)

    
    # ===== LOGO KAMPUS =====
    from utils.simda_reader import get_institusi
    institusi    = get_institusi()
    nama_kampus  = institusi.get('nama_resmi', 'Universitas Ichsan Gorontalo')
    nama_singkat = institusi.get('nama_singkat', 'UNISAN')
    logo_file    = institusi.get('logo', '')

    logo_loaded = False
    if logo_file:
        logo_path = os.path.join(
            settings.BASE_DIR, 'static', 'assets', logo_file
        )
        if os.path.exists(logo_path):
            try:
                img = ImageReader(logo_path)
                c.drawImage(img, 1.0*cm, tinggi - 3.8*cm,
                        2.8*cm, 2.8*cm,
                        preserveAspectRatio=True, mask='auto')
                logo_loaded = True
            except Exception as e:
                pass

    if not logo_loaded:
        c.setFillColor(colors.white)
        c.circle(2.2*cm, tinggi - 2.5*cm, 1.1*cm, fill=1, stroke=0)
        c.setFillColor(UNGU)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(2.2*cm, tinggi - 2.6*cm, nama_singkat[:4])

    # ===== TEKS HEADER =====
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 15)
    c.drawCentredString(lebar/2 + 1*cm, tinggi - 1.4*cm,
                        'UNIVERSITAS ICHSAN GORONTALO')
    c.setFont('Helvetica', 10)
    c.drawCentredString(lebar/2 + 1*cm, tinggi - 2.1*cm,
                        'Jl. Achmad Nadjamuddin No. 17, Kota Gorontalo')

    c.setFillColor(colors.HexColor('#fbbf24'))
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(lebar/2 + 1*cm, tinggi - 2.9*cm,
                        'KARTU PESERTA SELEKSI PMB')

    try:
        from master.models import PengaturanSistem
        tahun = PengaturanSistem.get().tahun_akademik_aktif
    except:
        tahun = '2025/2026'

    c.setFillColor(colors.white)
    c.setFont('Helvetica', 10)
    c.drawCentredString(lebar/2 + 1*cm, tinggi - 3.6*cm,
                        f'TAHUN AKADEMIK {tahun}')

    # ===== NOMOR KARTU =====
    try:
        kartu   = pendaftaran.kartu
        no_kartu = kartu.no_kartu
    except:
        no_kartu = f'PMB-{pendaftaran.no_pendaftaran}'

    c.setFillColor(colors.HexColor('#fef3c7'))
    c.roundRect(1.5*cm, tinggi - 6.3*cm, lebar - 3*cm, 1.5*cm, 6, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#92400e'))
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(lebar/2, tinggi - 5.2*cm, 'NOMOR PESERTA')
    c.setFillColor(HITAM)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(lebar/2, tinggi - 6.0*cm, no_kartu)

    # ===== FOTO =====
    foto_x = 1.5*cm
    foto_y = tinggi - 11.5*cm
    foto_w = 3.2*cm
    foto_h = 4.0*cm

    try:
        profil = pendaftaran.profil
        if profil.foto:
            foto_path = os.path.join(settings.MEDIA_ROOT, str(profil.foto))
            if os.path.exists(foto_path):
                img = ImageReader(foto_path)
                c.drawImage(img, foto_x, foto_y, foto_w, foto_h,
                           preserveAspectRatio=True, mask='auto')
            else:
                raise Exception()
        else:
            raise Exception()
    except:
        c.setFillColor(ABU_MUDA)
        c.rect(foto_x, foto_y, foto_w, foto_h, fill=1, stroke=0)
        c.setFillColor(ABU)
        c.setFont('Helvetica', 8)
        c.drawCentredString(foto_x + foto_w/2, foto_y + foto_h/2, 'FOTO')

    c.setStrokeColor(UNGU)
    c.setLineWidth(2)
    c.rect(foto_x, foto_y, foto_w, foto_h, fill=0, stroke=1)

    # ===== DATA PESERTA =====
    dx = foto_x + foto_w + 0.7*cm
    dy = tinggi - 6.8*cm

    try:
        profil       = pendaftaran.profil
        nama         = pendaftaran.user.get_full_name()
        nik          = profil.nik or '-'
        tgl_lahir    = profil.tgl_lahir.strftime('%d %B %Y') if profil.tgl_lahir else '-'
        jk           = profil.get_jenis_kelamin_display() if profil.jenis_kelamin else '-'
        asal_sekolah = (profil.asal_sekolah or '-')[:38]
    except:
        nama         = pendaftaran.user.get_full_name()
        nik          = '-'
        tgl_lahir    = '-'
        jk           = '-'
        asal_sekolah = '-'

    def label_nilai(label, nilai, y):
        c.setFillColor(ABU)
        c.setFont('Helvetica', 8)
        c.drawString(dx, y, label)
        c.setStrokeColor(ABU_MUDA)
        c.setLineWidth(0.5)
        c.line(dx, y - 0.1*cm, lebar - 1.5*cm, y - 0.1*cm)
        c.setFillColor(HITAM)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(dx, y - 0.55*cm, str(nilai))

    label_nilai('Nama Lengkap', nama,         dy)
    label_nilai('NIK',          nik,          dy - 1.1*cm)
    label_nilai('Tgl Lahir / JK', f'{tgl_lahir}  |  {jk}', dy - 2.2*cm)
    label_nilai('Asal Sekolah', asal_sekolah, dy - 3.3*cm)

    # ===== GARIS PEMISAH =====
    c.setStrokeColor(UNGU)
    c.setLineWidth(0.8)
    c.line(1.5*cm, tinggi - 12.0*cm, lebar - 1.5*cm, tinggi - 12.0*cm)

    # ===== INFO PENDAFTARAN =====
    iy = tinggi - 12.8*cm
    col_w = (lebar - 3.3*cm) / 2

    def kotak(label, nilai, x, y, w):
        c.setFillColor(ABU_MUDA)
        c.roundRect(x, y - 0.8*cm, w, 1.3*cm, 5, fill=1, stroke=0)
        c.setFillColor(UNGU)
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(x + 0.2*cm, y + 0.25*cm, label.upper())
        c.setFillColor(HITAM)
        c.setFont('Helvetica-Bold', 9.5)
        c.drawString(x + 0.2*cm, y - 0.45*cm, str(nilai)[:28] if nilai else '-')

    kotak('No. Pendaftaran', pendaftaran.no_pendaftaran,
          1.5*cm, iy, col_w)
    kotak('Jalur Penerimaan', pendaftaran.jalur.nama_jalur,
          1.5*cm + col_w + 0.3*cm, iy, col_w)

    iy -= 1.7*cm
    kotak('Program Studi', pendaftaran.prodi_pilihan_1.nama_prodi,
          1.5*cm, iy, col_w)
    kotak('Gelombang', pendaftaran.gelombang.nama_gelombang,
          1.5*cm + col_w + 0.3*cm, iy, col_w)

    # ===== JADWAL SELEKSI =====
    if jadwal:
        iy -= 1.7*cm
        c.setFillColor(UNGU)
        c.roundRect(1.5*cm, iy - 0.8*cm, lebar - 3*cm, 1.3*cm, 5, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(1.7*cm, iy + 0.25*cm, 'JADWAL SELEKSI')
        teks = (f'{jadwal.get_jenis_seleksi_display()} | '
                f'{jadwal.tgl_seleksi.strftime("%d %B %Y")} | '
                f'{jadwal.jam_mulai.strftime("%H:%M")}-'
                f'{jadwal.jam_selesai.strftime("%H:%M")} WIB')
        if jadwal.lokasi:
            teks += f' | {jadwal.lokasi}'
        c.setFont('Helvetica-Bold', 9)
        c.drawString(1.7*cm, iy - 0.45*cm, teks[:65])

    # ===== TATA TERTIB =====
    # Posisi tetap dari bawah agar tidak tabrakan dengan TTD
    tt_y = 9.5*cm  # dari bawah halaman

    c.setFillColor(HITAM)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(1.5*cm, tt_y, 'TATA TERTIB PESERTA SELEKSI:')

    rules = [
        '1. Hadir 30 menit sebelum seleksi dimulai.',
        '2. Membawa kartu ini dan KTP/identitas asli.',
        '3. Berpakaian rapi dan sopan (kemeja/baju berkerah).',
        '4. Tidak menggunakan alat komunikasi selama seleksi.',
        '5. Terlambat >15 menit tidak diperkenankan masuk.',
        '6. Ikuti petunjuk panitia selama seleksi berlangsung.',
    ]
    c.setFont('Helvetica', 8.5)
    c.setFillColor(ABU)
    for i, r in enumerate(rules):
        c.drawString(1.5*cm, tt_y - (i+1)*0.45*cm, r)

    # ===== TANDA TANGAN =====
    # Posisi tetap dari bawah
    ttd_y = 2.5*cm

    
    # TTD Panitia (kanan) — tanpa bingkai
    c.setFillColor(ABU)
    c.setFont('Helvetica', 8)
    c.drawCentredString(lebar - 4*cm, ttd_y + 3.0*cm, 'Panitia PMB UNISAN')

    # Garis TTD
    c.setStrokeColor(HITAM)
    c.setLineWidth(0.7)
    c.line(lebar - 6.5*cm, ttd_y + 0.5*cm, lebar - 1.5*cm, ttd_y + 0.5*cm)
    c.setFillColor(ABU)
    c.setFont('Helvetica', 8)
    c.drawCentredString(lebar - 4*cm, ttd_y + 0.2*cm, 'Panitia PMB UNISAN')

    # TTD Peserta (kiri)
    c.setFillColor(HITAM)
    c.setFont('Helvetica', 8.5)
    c.drawString(1.5*cm, ttd_y + 3.0*cm, 'Gorontalo, .............................')
    c.drawString(1.5*cm, ttd_y + 2.3*cm, 'Peserta,')
    c.drawString(1.5*cm, ttd_y + 0.3*cm, '(__________________________)')

    # ===== FOOTER =====
    c.setFillColor(UNGU)
    c.rect(0, 0, lebar, 1.0*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(lebar/2, 0.35*cm,
        f'PMB UNISAN {tahun}  |  pmb.unisan.ac.id  |  '
        f'Kartu ini hanya berlaku untuk keperluan seleksi PMB UNISAN Gorontalo')

    # ===== WATERMARK =====
    c.saveState()
    c.setFillColor(UNGU)
    c.setFillAlpha(0.035)
    c.setFont('Helvetica-Bold', 55)
    c.translate(lebar/2, tinggi/2)
    c.rotate(40)
    c.drawCentredString(0, 0, 'PMB UNISAN Gorontalo')
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def buat_kartu_massal(pendaftaran_list, jadwal=None):
    from PyPDF2 import PdfMerger
    merger = PdfMerger()
    for p in pendaftaran_list:
        try:
            buf = buat_kartu_peserta(p, jadwal)
            merger.append(buf)
        except Exception as e:
            pass
    output = BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return output

def buat_formulir_pendaftaran(pendaftaran):
    """
    Generate formulir pendaftaran lengkap PDF — untuk arsip peserta & panitia
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    lebar, tinggi = A4

    from utils.simda_reader import get_institusi
    institusi    = get_institusi()
    nama_kampus  = institusi.get('nama_resmi', 'Universitas Ichsan Gorontalo')
    nama_singkat = institusi.get('nama_singkat', 'UNISAN')
    logo_file    = institusi.get('logo', '')

    try:
        from master.models import PengaturanSistem
        tahun = PengaturanSistem.get().tahun_akademik_aktif
    except:
        tahun = '2025/2026'

    try:
        profil = pendaftaran.profil
    except:
        profil = None

    # ===== HEADER =====
    # Logo - naikkan posisi
    logo_loaded = False
    if logo_file:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'assets', logo_file)
        if os.path.exists(logo_path):
            try:
                img = ImageReader(logo_path)
                c.drawImage(img, 1.0*cm, tinggi - 3.0*cm,
                        2.5*cm, 2.5*cm,
                        preserveAspectRatio=True, mask='auto')
                logo_loaded = True
            except:
                pass

    if not logo_loaded:
        c.setFillColor(UNGU)
        c.circle(2.2*cm, tinggi - 1.8*cm, 1.0*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(2.2*cm, tinggi - 1.9*cm, nama_singkat[:4])

    # Teks header tengah
    c.setFillColor(HITAM)
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(lebar/2, tinggi - 0.9*cm, nama_kampus.upper())
    c.setFont('Helvetica', 9)
    c.drawCentredString(lebar/2, tinggi - 1.5*cm,
        f'{institusi.get("alamat", "")} | Telp: {institusi.get("telepon", "")}')
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(lebar/2, tinggi - 2.1*cm,
        f'FORMULIR PENDAFTARAN MAHASISWA BARU {tahun}')

    # Garis bawah header — di atas foto
    c.setStrokeColor(UNGU)
    c.setLineWidth(2)
    c.line(1.0*cm, tinggi - 3.1*cm, lebar - 1.0*cm, tinggi - 3.1*cm)
    c.setLineWidth(0.5)
    c.line(1.0*cm, tinggi - 3.3*cm, lebar - 1.0*cm, tinggi - 3.3*cm)

    # Foto 3x4 — di dalam area DATA PENDAFTARAN, sebelah kanan
    foto_w = 2.8*cm
    foto_h = 3.7*cm
    foto_x = lebar - 1.2*cm - foto_w
    foto_y = tinggi - 3.3*cm - foto_h  # tepat di bawah garis header

    foto_loaded = False
    if profil and profil.foto:
        foto_path = os.path.join(settings.MEDIA_ROOT, str(profil.foto))
        if os.path.exists(foto_path):
            try:
                img = ImageReader(foto_path)
                c.drawImage(img, foto_x, foto_y, foto_w, foto_h,
                        preserveAspectRatio=False, mask='auto')
                foto_loaded = True
            except:
                pass

    if not foto_loaded:
        c.setFillColor(ABU_MUDA)
        c.rect(foto_x, foto_y, foto_w, foto_h, fill=1, stroke=0)
        c.setFillColor(ABU)
        c.setFont('Helvetica', 7)
        c.drawCentredString(foto_x + foto_w/2, foto_y + foto_h/2 + 0.2*cm, 'PAS FOTO')
        c.drawCentredString(foto_x + foto_w/2, foto_y + foto_h/2 - 0.3*cm, '3 x 4')

    c.setStrokeColor(HITAM)
    c.setLineWidth(1)
    c.rect(foto_x, foto_y, foto_w, foto_h, fill=0, stroke=1)

    # Label foto
    c.setFillColor(ABU)
    c.setFont('Helvetica', 7)
    c.drawCentredString(foto_x + foto_w/2, foto_y - 0.3*cm, 'Pas Foto 3x4')

    # Posisi awal konten — setelah garis header
    y = tinggi - 3.6*cm
    # ===== HELPER FUNCTIONS =====
    def judul_seksi(teks, y):
        c.setFillColor(UNGU)
        c.rect(1.0*cm, y - 0.35*cm, lebar - 2.0*cm, 0.5*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(1.2*cm, y - 0.18*cm, teks.upper())
        return y - 0.7*cm

    def baris(label, nilai, x, y, lebar_label=4.5*cm, lebar_nilai=None):
        if lebar_nilai is None:
            lebar_nilai = lebar - x - 1.0*cm - lebar_label
        c.setFillColor(ABU)
        c.setFont('Helvetica', 8)
        c.drawString(x, y, label)
        c.setFillColor(HITAM)
        c.setFont('Helvetica', 9)
        nilai_str = str(nilai) if nilai else '-'
        c.drawString(x + lebar_label, y, nilai_str[:50])
        c.setStrokeColor(ABU_MUDA)
        c.setLineWidth(0.3)
        c.line(x + lebar_label, y - 0.1*cm,
            x + lebar_label + lebar_nilai, y - 0.1*cm)
        return y - 0.55*cm

    def baris2(label1, nilai1, label2, nilai2, y, lebar_label=3.5*cm):
        tengah = lebar/2
        baris(label1, nilai1, 1.0*cm, y, lebar_label)
        baris(label2, nilai2, tengah, y, lebar_label)
        return y - 0.55*cm
        
    # ===== A. DATA PENDAFTARAN =====
    y = judul_seksi('A. Data Pendaftaran', y)
    y -= 0.2*cm

    y = baris2('No. Pendaftaran',
               pendaftaran.no_pendaftaran,
               'Tgl. Pendaftaran',
               pendaftaran.tgl_daftar.strftime('%d %B %Y') if pendaftaran.tgl_daftar else '-',
               y)
    y = baris2('Jalur Penerimaan',
               pendaftaran.jalur.nama_jalur,
               'Gelombang',
               pendaftaran.gelombang.nama_gelombang,
               y)
    y = baris2('Prodi Pilihan 1',
               pendaftaran.prodi_pilihan_1.nama_prodi,
               'Prodi Pilihan 2',
               pendaftaran.prodi_pilihan_2.nama_prodi if pendaftaran.prodi_pilihan_2 else '-',
               y)
    y = baris2('Status',
               pendaftaran.get_status_display(),
               'Kode Referral',
               pendaftaran.kode_referral or '-',
               y)
    y -= 0.3*cm

    # ===== B. DATA DIRI =====
    y = judul_seksi('B. Data Diri', y)
    y -= 0.2*cm

    nama = pendaftaran.user.get_full_name()
    y = baris('Nama Lengkap', nama, 1.0*cm, y)
    y = baris2('NIK',
               profil.nik if profil else '-',
               'Kewarganegaraan',
               profil.get_kewarganegaraan_display() if profil and profil.kewarganegaraan else '-',
               y)
    y = baris2('Tempat Lahir',
               profil.tempat_lahir if profil else '-',
               'Tanggal Lahir',
               profil.tgl_lahir.strftime('%d %B %Y') if profil and profil.tgl_lahir else '-',
               y)
    y = baris2('Jenis Kelamin',
               profil.get_jenis_kelamin_display() if profil and profil.jenis_kelamin else '-',
               'Agama',
               profil.agama_nama if profil else '-',
               y)
    y = baris2('Status Nikah',
               profil.get_status_nikah_display() if profil and profil.status_nikah else '-',
               'Ukuran Baju',
               profil.ukuran_baju if profil else '-',
               y)
    y = baris('Kebutuhan Khusus',
              profil.kebutuhan_khusus if profil and profil.kebutuhan_khusus else '-',
              1.0*cm, y)
    y -= 0.3*cm

    # ===== C. ALAMAT =====
    y = judul_seksi('C. Alamat Domisili', y)
    y -= 0.2*cm

    y = baris('Alamat Lengkap',
              profil.alamat_lengkap if profil else '-',
              1.0*cm, y)
    y = baris2('Provinsi',
               profil.provinsi_nama if profil else '-',
               'Kab/Kota',
               profil.kabupaten_kota_nama if profil else '-',
               y)
    y = baris2('Kecamatan',
               profil.kecamatan_nama if profil else '-',
               'Kode Pos',
               profil.kode_pos if profil else '-',
               y)
    y = baris2('Email',
               pendaftaran.user.email,
               'No. HP / WA',
               pendaftaran.user.no_hp or '-',
               y)
    y -= 0.3*cm

    # ===== D. DATA ORANG TUA =====
    y = judul_seksi('D. Data Orang Tua / Wali', y)
    y -= 0.2*cm

    y = baris2('Nama Ayah',
               profil.nama_ayah if profil else '-',
               'Pekerjaan Ayah',
               profil.pekerjaan_ayah if profil else '-',
               y)
    y = baris2('Nama Ibu',
               profil.nama_ibu if profil else '-',
               'Pekerjaan Ibu',
               profil.pekerjaan_ibu if profil else '-',
               y)
    y = baris2('Nama Wali',
               profil.nama_wali if profil and profil.nama_wali else '-',
               'No. HP Ortu/Wali',
               profil.no_hp_ortu if profil else '-',
               y)
    y -= 0.3*cm

    # ===== E. DATA PENDIDIKAN =====
    y = judul_seksi('E. Data Pendidikan', y)
    y -= 0.2*cm

    y = baris('Asal Sekolah',
              profil.asal_sekolah if profil else '-',
              1.0*cm, y)
    y = baris2('Jurusan',
               profil.jurusan_sekolah if profil else '-',
               'Tahun Lulus',
               str(profil.tahun_lulus) if profil and profil.tahun_lulus else '-',
               y)
    y = baris2('No. Ijazah',
               profil.no_ijazah if profil else '-',
               'Nilai Rata-rata',
               str(profil.nilai_rata_rata) if profil and profil.nilai_rata_rata else '-',
               y)
    y = baris('Prestasi',
              profil.prestasi if profil and profil.prestasi else '-',
              1.0*cm, y)
    y -= 0.3*cm

    # ===== F. SUMBER INFORMASI =====
    if y > 4.0*cm:
        y = judul_seksi('F. Sumber Informasi PMB', y)
        y -= 0.2*cm
        sumber = profil.get_sumber_informasi_display() if profil and profil.sumber_informasi else '-'
        if profil and profil.sumber_informasi_lain:
            sumber += f' ({profil.sumber_informasi_lain})'
        y = baris('Sumber Informasi', sumber, 1.0*cm, y)
        y -= 0.3*cm

    # ===== TANDA TANGAN =====
    ttd_y = 2.8*cm

    c.setFillColor(HITAM)
    c.setFont('Helvetica', 8.5)

    # TTD Peserta (kiri)
    c.drawString(1.5*cm, ttd_y + 2.5*cm, 'Yang Bertanda Tangan,')
    c.drawString(1.5*cm, ttd_y + 2.0*cm, 'Peserta')
    c.setStrokeColor(HITAM)
    c.setLineWidth(0.5)
    c.line(1.5*cm, ttd_y + 0.4*cm, 6.0*cm, ttd_y + 0.4*cm)
    c.setFont('Helvetica', 8)
    c.drawCentredString(3.75*cm, ttd_y + 0.1*cm,
                        f'( {nama} )')

    # TTD Panitia (kanan)
    c.setFont('Helvetica', 8.5)
    c.drawString(lebar - 6.5*cm, ttd_y + 2.5*cm, 'Mengetahui,')
    c.drawString(lebar - 6.5*cm, ttd_y + 2.0*cm, 'Panitia PMB UNISAN')
    c.line(lebar - 6.5*cm, ttd_y + 0.4*cm, lebar - 1.5*cm, ttd_y + 0.4*cm)
    c.setFont('Helvetica', 8)
    c.drawCentredString(lebar - 4.0*cm, ttd_y + 0.1*cm, '(............................)')

    # ===== FOOTER =====
    c.setFillColor(UNGU)
    c.rect(0, 0, lebar, 1.0*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(lebar/2, 0.35*cm,
        f'Formulir Pendaftaran PMB UNISAN {tahun}  |  '
        f'Dicetak: {__import__("datetime").datetime.now().strftime("%d/%m/%Y %H:%M")}  |  '
        f'pmb.unisan-g.id')

    # ===== WATERMARK =====
    c.saveState()
    c.setFillColor(UNGU)
    c.setFillAlpha(0.03)
    c.setFont('Helvetica-Bold', 50)
    c.translate(lebar/2, tinggi/2)
    c.rotate(40)
    c.drawCentredString(0, 0, 'PMB UNISAN')
    c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer