import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from pendaftaran.models import Pendaftaran, ProfilPendaftar
from dokumen.models import DokumenPendaftar
from master.models import JalurPenerimaan, GelombangPenerimaan, PengaturanSistem
from chatbot.models import KnowledgeBase

logger = logging.getLogger(__name__)


def cek_admin(user):
    return user.is_authenticated and user.role in [
        'admin_pmb', 'operator_pmb', 'panitia_seleksi', 'pimpinan'
    ]


def get_sidebar_counts():
    """Hitung badge notifikasi untuk sidebar"""
    return {
        'pending_verifikasi': Pendaftaran.objects.filter(status='LENGKAP').count(),
        'pending_dokumen': DokumenPendaftar.objects.filter(status_verifikasi='menunggu').count(),
    }


@login_required
def dashboard(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    # Statistik utama
    total        = Pendaftaran.objects.count()
    hari_ini     = Pendaftaran.objects.filter(
        tgl_daftar__date=timezone.now().date()).count()
    perlu_verif  = Pendaftaran.objects.filter(status='LENGKAP').count()
    dok_pending  = DokumenPendaftar.objects.filter(status_verifikasi='menunggu').count()
    lulus        = Pendaftaran.objects.filter(status='LULUS_SELEKSI').count()
    daftar_ulang = Pendaftaran.objects.filter(status='DAFTAR_ULANG').count()
    draft        = Pendaftaran.objects.filter(status='DRAFT').count()
    tidak_lulus  = Pendaftaran.objects.filter(status='TIDAK_LULUS').count()

    # Per jalur
    per_jalur = Pendaftaran.objects.values(
        'jalur__nama_jalur'
    ).annotate(total=Count('id')).order_by('-total')

    # Per prodi
    per_prodi = Pendaftaran.objects.values(
        'prodi_pilihan_1__nama_prodi'
    ).annotate(total=Count('id')).order_by('-total')[:8]

    # 10 terbaru
    terbaru = Pendaftaran.objects.select_related(
        'user', 'jalur', 'prodi_pilihan_1', 'gelombang'
    ).order_by('-tgl_daftar')[:10]

    pengaturan = PengaturanSistem.get()

    context = {
        'total': total, 'hari_ini': hari_ini,
        'perlu_verif': perlu_verif, 'dok_pending': dok_pending,
        'lulus': lulus, 'daftar_ulang': daftar_ulang,
        'draft': draft, 'tidak_lulus': tidak_lulus,
        'per_jalur': per_jalur, 'per_prodi': per_prodi,
        'terbaru': terbaru, 'pengaturan': pengaturan,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/dashboard.html', context)


@login_required
def pendaftar(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    # Filter
    status   = request.GET.get('status', '')
    jalur    = request.GET.get('jalur', '')
    gelombang= request.GET.get('gelombang', '')
    cari     = request.GET.get('q', '')

    qs = Pendaftaran.objects.select_related(
        'user', 'jalur', 'prodi_pilihan_1', 'gelombang'
    ).order_by('-tgl_daftar')

    if status:   qs = qs.filter(status=status)
    if jalur:    qs = qs.filter(jalur_id=jalur)
    if gelombang:qs = qs.filter(gelombang_id=gelombang)
    if cari:
        qs = qs.filter(
            Q(user__first_name__icontains=cari) |
            Q(user__last_name__icontains=cari) |
            Q(user__email__icontains=cari) |
            Q(no_pendaftaran__icontains=cari)
        )

    context = {
        'pendaftar_list': qs,
        'jalur_list':     JalurPenerimaan.objects.filter(status='aktif'),
        'gelombang_list': GelombangPenerimaan.objects.all(),
        'status_choices': Pendaftaran.STATUS_CHOICES,
        'filter_status':  status,
        'filter_jalur':   jalur,
        'filter_gelombang': gelombang,
        'filter_cari':    cari,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/pendaftar.html', context)


@login_required
def detail_pendaftar(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    pendaftaran = get_object_or_404(
        Pendaftaran.objects.select_related('user', 'jalur', 'gelombang',
        'prodi_pilihan_1', 'prodi_pilihan_2'), pk=pk
    )
    try:
        profil = pendaftaran.profil
    except:
        profil = None

    dokumen_list = DokumenPendaftar.objects.filter(
        pendaftaran=pendaftaran
    ).select_related('persyaratan')

    log_list = pendaftaran.log_status.all().order_by('-tgl_perubahan')

    context = {
        'pendaftaran': pendaftaran,
        'profil': profil,
        'dokumen_list': dokumen_list,
        'log_list': log_list,
        'status_choices': Pendaftaran.STATUS_CHOICES,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/detail_pendaftar.html', context)


@login_required
def ubah_status(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    if request.method == 'POST':
        pendaftaran = get_object_or_404(Pendaftaran, pk=pk)
        status_baru  = request.POST.get('status_baru')
        keterangan   = request.POST.get('keterangan', '')

        from pendaftaran.models import LogStatusPendaftaran
        LogStatusPendaftaran.objects.create(
            pendaftaran=pendaftaran,
            status_lama=pendaftaran.status,
            status_baru=status_baru,
            keterangan=keterangan,
            diubah_oleh=request.user,
        )
        pendaftaran.status = status_baru
        pendaftaran.save()
        messages.success(request, f'Status berhasil diubah ke {status_baru}.')

    return redirect('admin_pmb:detail_pendaftar', pk=pk)


@login_required
def verifikasi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    dok_list = DokumenPendaftar.objects.filter(
        status_verifikasi='menunggu'
    ).select_related('pendaftaran__user', 'persyaratan').order_by('tgl_upload')

    context = {
        'dok_list': dok_list,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/verifikasi.html', context)


@login_required
def verif_acc(request, dok_id):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    if request.method == 'POST':
        dok = get_object_or_404(DokumenPendaftar, pk=dok_id)
        dok.status_verifikasi = 'terverifikasi'
        dok.tgl_verifikasi    = timezone.now()
        dok.diverifikasi_oleh = request.user
        dok.catatan_verifikasi = request.POST.get('catatan', '')
        dok.save()
        messages.success(request, f'Dokumen "{dok.nama_dokumen}" berhasil diverifikasi.')
    return redirect('admin_pmb:verifikasi')


@login_required
def verif_tolak(request, dok_id):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    if request.method == 'POST':
        dok = get_object_or_404(DokumenPendaftar, pk=dok_id)
        dok.status_verifikasi  = 'ditolak'
        dok.tgl_verifikasi     = timezone.now()
        dok.diverifikasi_oleh  = request.user
        dok.catatan_verifikasi = request.POST.get('catatan', '')
        dok.save()
        messages.warning(request, f'Dokumen "{dok.nama_dokumen}" ditolak.')
    return redirect('admin_pmb:verifikasi')


@login_required
def pembayaran(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    return render(request, 'admin_pmb/placeholder.html', {
        'page_title': 'Pembayaran',
        **get_sidebar_counts()
    })



@login_required
def seleksi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    return render(request, 'admin_pmb/placeholder.html', {
        'page_title': 'Seleksi',
        **get_sidebar_counts()
    })


@login_required
def hasil(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    return render(request, 'admin_pmb/placeholder.html', {
        'page_title': 'Hasil Penerimaan',
        **get_sidebar_counts()
    })

@login_required
def master(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    return render(request, 'admin_pmb/placeholder.html', {
        'page_title': 'Master Data',
        **get_sidebar_counts()
    })

@login_required
def konten(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    return render(request, 'admin_pmb/placeholder.html', {
        'page_title': 'Konten & Promosi',
        **get_sidebar_counts()
    })


@login_required
def afiliasi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from afiliasi.models import Recruiter, KomisiReferral, PencairanKomisi
    from django.db.models import Sum

    status_filter = request.GET.get('status', 'menunggu')
    status_tabs = [
        ('menunggu',  'Menunggu Verifikasi', '#f59e0b'),
        ('aktif',     'Aktif',               '#10b981'),
        ('nonaktif',  'Ditolak',             '#ef4444'),
        ('suspend',   'Suspend',             '#94a3b8'),
    ]

    recruiter_list = Recruiter.objects.filter(
        status=status_filter
    ).select_related('user').order_by('-tgl_bergabung')

    total_menunggu  = Recruiter.objects.filter(status='menunggu').count()
    total_aktif     = Recruiter.objects.filter(status='aktif').count()
    total_komisi    = KomisiReferral.objects.filter(status='approved').aggregate(
        total=Sum('jumlah_komisi'))['total'] or 0
    total_pencairan = PencairanKomisi.objects.filter(status='pending').count()

    context = {
        'recruiter_list':  recruiter_list,
        'status_filter':   status_filter,
        'status_tabs':     status_tabs,
        'total_menunggu':  total_menunggu,
        'total_aktif':     total_aktif,
        'total_komisi':    total_komisi,
        'total_pencairan': total_pencairan,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/afiliasi.html', context)


@login_required
def laporan(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    return render(request, 'admin_pmb/placeholder.html', {
        'page_title': 'Export Laporan',
        **get_sidebar_counts()
    })

@login_required
def chatbot_kb(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    kb_list = KnowledgeBase.objects.all().order_by('kategori', 'urutan_prioritas')
    return render(request, 'admin_pmb/chatbot_kb.html', {
        'kb_list': kb_list,
        **get_sidebar_counts()
    })

@login_required
def afiliasi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from afiliasi.models import Recruiter, KomisiReferral, PencairanKomisi
    from django.db.models import Sum

    status_filter = request.GET.get('status', 'menunggu')

    recruiter_list = Recruiter.objects.filter(
        status=status_filter
    ).select_related('user').order_by('-tgl_bergabung')

    # Statistik
    total_menunggu  = Recruiter.objects.filter(status='menunggu').count()
    total_aktif     = Recruiter.objects.filter(status='aktif').count()
    total_komisi    = KomisiReferral.objects.filter(status='approved').aggregate(
        total=Sum('jumlah_komisi'))['total'] or 0
    total_pencairan = PencairanKomisi.objects.filter(status='pending').count()

    context = {
        'recruiter_list':  recruiter_list,
        'status_filter':   status_filter,
        'total_menunggu':  total_menunggu,
        'total_aktif':     total_aktif,
        'total_komisi':    total_komisi,
        'total_pencairan': total_pencairan,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/afiliasi.html', context)


@login_required
def afiliasi_approve(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    if request.method == 'POST':
        from afiliasi.models import Recruiter
        rec = get_object_or_404(Recruiter, pk=pk)
        rec.status = 'aktif'
        rec.save()
        messages.success(request, f'Recruiter {rec.user.get_full_name()} berhasil diaktifkan!')
    return redirect('admin_pmb:afiliasi')


@login_required
def afiliasi_tolak(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    if request.method == 'POST':
        from afiliasi.models import Recruiter
        rec = get_object_or_404(Recruiter, pk=pk)
        alasan = request.POST.get('alasan', '')
        rec.status  = 'nonaktif'
        rec.catatan = f'DITOLAK: {alasan}'
        rec.save()
        messages.warning(request, f'Recruiter {rec.user.get_full_name()} ditolak.')
    return redirect('admin_pmb:afiliasi')


@login_required
def afiliasi_detail(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')
    from afiliasi.models import Recruiter, KomisiReferral
    rec = get_object_or_404(Recruiter.objects.select_related('user'), pk=pk)
    komisi_list = KomisiReferral.objects.filter(
        recruiter=rec).select_related('pendaftaran__user').order_by('-tgl_komisi')
    context = {
        'rec': rec,
        'komisi_list': komisi_list,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/afiliasi_detail.html', context)
