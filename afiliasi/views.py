import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum


from .models import Recruiter, KomisiReferral, PencairanKomisi, PengaturanAfiliasi
from pendaftaran.models import Pendaftaran

logger = logging.getLogger(__name__)


def generate_kode_referral(nama):
    import re
    nama_bersih = re.sub(r'[^a-zA-Z]', '', nama).upper()[:4]
    kode = f"{nama_bersih}{str(uuid.uuid4())[:4].upper()}"
    while Recruiter.objects.filter(kode_referral=kode).exists():
        kode = f"{nama_bersih}{str(uuid.uuid4())[:4].upper()}"
    return kode


def info_recruiter(request):
    from master.models import PengaturanSistem
    pengaturan     = PengaturanAfiliasi.get()
    sys_pengaturan = PengaturanSistem.get()
    steps = [
        'Buat akun PMB UNISAN atau login jika sudah punya akun',
        'Isi form pendaftaran recruiter dengan data rekening',
        'Tunggu verifikasi panitia PMB (1x24 jam kerja)',
        'Akun aktif — dapatkan kode referral unik Anda',
        'Bagikan link referral dan pantau komisi di dashboard',
    ]
    return render(request, 'afiliasi/info_recruiter.html', {
        'pengaturan':     pengaturan,
        'sys_pengaturan': sys_pengaturan,
        'steps':          steps,
    })


@login_required
def daftar_recruiter(request):
    """Form pendaftaran recruiter — perlu login"""
    # Sudah jadi recruiter
    if hasattr(request.user, 'recruiter'):
        rec = request.user.recruiter
        if rec.status == 'menunggu':
            return render(request, 'afiliasi/menunggu_verifikasi.html', {'recruiter': rec})
        return redirect('afiliasi:dashboard')

    pengaturan     = PengaturanAfiliasi.get()
    sys_pengaturan = __import__('master.models', fromlist=['PengaturanSistem']).PengaturanSistem.get()

    if request.method == 'POST':
        bank          = request.POST.get('bank', '').strip()
        no_rekening   = request.POST.get('no_rekening', '').strip()
        nama_rekening = request.POST.get('nama_rekening', '').strip()
        motivasi      = request.POST.get('motivasi', '').strip()

        if not all([bank, no_rekening, nama_rekening]):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect('afiliasi:daftar')

        kode = generate_kode_referral(request.user.first_name or request.user.username)

        Recruiter.objects.create(
            user          = request.user,
            kode_referral = kode,
            bank          = bank,
            no_rekening   = no_rekening,
            nama_rekening = nama_rekening,
            catatan       = motivasi,
            status        = 'menunggu',
        )
        messages.success(request, 'Pendaftaran berhasil! Tunggu verifikasi dari panitia PMB.')
        return redirect('afiliasi:daftar')

    return render(request, 'afiliasi/daftar_recruiter.html', {
        'pengaturan':     pengaturan,
        'sys_pengaturan': sys_pengaturan,
    })


@login_required
def dashboard_recruiter(request):
    """Dashboard recruiter — hanya untuk yang sudah aktif"""
    if not hasattr(request.user, 'recruiter'):
        return redirect('afiliasi:daftar')

    recruiter = request.user.recruiter

    if recruiter.status == 'menunggu':
        return render(request, 'afiliasi/menunggu_verifikasi.html', {'recruiter': recruiter})

    if recruiter.status in ['nonaktif', 'suspend']:
        messages.error(request, 'Akun recruiter Anda tidak aktif.')
        return redirect('beranda')

    pengaturan     = PengaturanAfiliasi.get()
    total_referral = recruiter.total_referral
    komisi_pending = KomisiReferral.objects.filter(
        recruiter=recruiter, status='pending'
    ).aggregate(total=Sum('jumlah_komisi'))['total'] or 0
    komisi_approved= KomisiReferral.objects.filter(
        recruiter=recruiter, status='approved'
    ).aggregate(total=Sum('jumlah_komisi'))['total'] or 0
    komisi_paid    = KomisiReferral.objects.filter(
        recruiter=recruiter, status='paid'
    ).aggregate(total=Sum('jumlah_komisi'))['total'] or 0
    saldo          = komisi_approved

    syarat_map = {
        1: pengaturan.syarat_naik_level_2,
        2: pengaturan.syarat_naik_level_3,
        3: pengaturan.syarat_naik_level_4,
        4: None,
    }
    syarat_naik    = syarat_map.get(recruiter.level)
    progress_level = 0
    if syarat_naik:
        syarat_prev = {
            1: 0,
            2: pengaturan.syarat_naik_level_2,
            3: pengaturan.syarat_naik_level_3,
        }
        prev = syarat_prev.get(recruiter.level, 0)
        progress_level = min(100, int(
            ((total_referral - prev) / max(syarat_naik - prev, 1)) * 100
        ))

    referral_list = Pendaftaran.objects.filter(
        kode_referral=recruiter.kode_referral
    ).select_related('user', 'prodi_pilihan_1').order_by('-tgl_daftar')[:10]

    komisi_list = KomisiReferral.objects.filter(
        recruiter=recruiter
    ).select_related('pendaftaran__user').order_by('-tgl_komisi')[:10]

    # Ambil 4 template flyer aktif untuk section "Bagikan Flyer"
    from .models import TemplateFlyer
    templates_flyer = TemplateFlyer.objects.filter(is_aktif=True).order_by('urutan')

    link_referral = f"{request.scheme}://{request.get_host()}/accounts/daftar/?ref={recruiter.kode_referral}"

    context = {
        'recruiter':       recruiter,
        'pengaturan':      pengaturan,
        'total_referral':  total_referral,
        'komisi_pending':  komisi_pending,
        'komisi_approved': komisi_approved,
        'komisi_paid':     komisi_paid,
        'saldo':           saldo,
        'syarat_naik':     syarat_naik,
        'progress_level':  progress_level,
        'referral_list':   referral_list,
        'komisi_list':     komisi_list,
        'link_referral':   link_referral,
        'templates_flyer': templates_flyer,
    }
    return render(request, 'afiliasi/dashboard_recruiter.html', context)


@login_required
def request_pencairan(request):
    if not hasattr(request.user, 'recruiter'):
        return redirect('afiliasi:daftar')

    recruiter  = request.user.recruiter
    pengaturan = PengaturanAfiliasi.get()

    if recruiter.status != 'aktif':
        messages.error(request, 'Akun recruiter tidak aktif.')
        return redirect('afiliasi:dashboard')

    saldo = KomisiReferral.objects.filter(
        recruiter=recruiter, status='approved'
    ).aggregate(total=Sum('jumlah_komisi'))['total'] or 0

    if request.method == 'POST':
        jumlah = float(request.POST.get('jumlah', 0))
        if jumlah < float(pengaturan.min_pencairan):
            messages.error(request, f'Minimal pencairan Rp {pengaturan.min_pencairan:,.0f}')
        elif jumlah > float(saldo):
            messages.error(request, 'Saldo tidak mencukupi')
        else:
            PencairanKomisi.objects.create(
                recruiter     = recruiter,
                jumlah        = jumlah,
                bank          = recruiter.bank,
                no_rekening   = recruiter.no_rekening,
                nama_rekening = recruiter.nama_rekening,
            )
            messages.success(request, f'Request pencairan Rp {jumlah:,.0f} berhasil!')

    return redirect('afiliasi:dashboard')

# ============================================================
# FLYER GENERATOR VIEWS
# ============================================================

from django.http import HttpResponse, Http404
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_control


def _get_recruiter_aktif(request):
    """Helper: ambil Recruiter aktif milik user yang login.

    Raise Http404 jika user belum jadi recruiter atau status tidak aktif.
    """
    if not hasattr(request.user, 'recruiter'):
        raise Http404("Anda belum terdaftar sebagai recruiter.")

    recruiter = request.user.recruiter
    if recruiter.status != 'aktif':
        raise Http404("Akun recruiter belum aktif atau telah dinonaktifkan.")

    return recruiter


def _get_base_url(request):
    """Build base URL dari request agar QR code link mengikuti domain aktual."""
    return f"{request.scheme}://{request.get_host()}"


@login_required
@require_GET
@cache_control(private=True, max_age=3600)
def flyer_preview(request, kode_template):
    """Preview flyer inline (untuk <img src=...>)."""
    from afiliasi.models import TemplateFlyer
    from afiliasi.services.flyer_generator import FlyerGenerator

    recruiter = _get_recruiter_aktif(request)
    get_object_or_404(TemplateFlyer, kode=kode_template, is_aktif=True)

    gen = FlyerGenerator(recruiter, base_url=_get_base_url(request))
    png_bytes = gen.get_png_bytes(kode_template)

    response = HttpResponse(png_bytes, content_type='image/png')
    response['Cache-Control'] = 'private, max-age=3600'
    return response


@login_required
@require_GET
def flyer_download_png(request, kode_template):
    """Download PNG dengan header attachment."""
    from afiliasi.models import TemplateFlyer
    from afiliasi.services.flyer_generator import FlyerGenerator

    recruiter = _get_recruiter_aktif(request)
    get_object_or_404(TemplateFlyer, kode=kode_template, is_aktif=True)

    gen = FlyerGenerator(recruiter, base_url=_get_base_url(request))
    png_bytes = gen.get_png_bytes(kode_template)

    filename = f"flyer-pmb-unisan-{kode_template}-{recruiter.kode_referral}.png"
    response = HttpResponse(png_bytes, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_GET
def flyer_download_pdf(request, kode_template):
    """Download PDF (khusus template 'cetak' dalam ukuran A5)."""
    from afiliasi.models import TemplateFlyer
    from afiliasi.services.flyer_generator import FlyerGenerator

    if kode_template != 'cetak':
        raise Http404("PDF hanya tersedia untuk template 'cetak'.")

    recruiter = _get_recruiter_aktif(request)
    get_object_or_404(TemplateFlyer, kode=kode_template, is_aktif=True)

    gen = FlyerGenerator(recruiter, base_url=_get_base_url(request))
    pdf_bytes = gen.get_pdf_bytes(kode_template)

    filename = f"flyer-pmb-unisan-cetak-{recruiter.kode_referral}.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response