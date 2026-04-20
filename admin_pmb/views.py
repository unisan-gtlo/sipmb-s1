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

    status    = request.GET.get('status', '')
    jalur     = request.GET.get('jalur', '')
    gelombang = request.GET.get('gelombang', '')
    cari      = request.GET.get('q', '')

    qs = Pendaftaran.objects.select_related(
        'user', 'jalur', 'prodi_pilihan_1', 'gelombang'
    ).order_by('-tgl_daftar')

    if status:    qs = qs.filter(status=status)
    if jalur:     qs = qs.filter(jalur_id=jalur)
    if gelombang: qs = qs.filter(gelombang_id=gelombang)
    if cari:
        qs = qs.filter(
            Q(user__first_name__icontains=cari) |
            Q(user__last_name__icontains=cari)  |
            Q(user__email__icontains=cari)       |
            Q(no_pendaftaran__icontains=cari)
        )

    # Ambil mapping kode_referral → nama recruiter
    from afiliasi.models import Recruiter
    recruiter_map = {
        r.kode_referral: r.user.get_full_name()
        for r in Recruiter.objects.select_related('user').all()
    }

    # Tambahkan nama recruiter ke setiap pendaftar
    pendaftar_list = list(qs)
    for p in pendaftar_list:
        p.nama_recruiter = recruiter_map.get(p.kode_referral, '')

    context = {
        'pendaftar_list':   pendaftar_list,
        'jalur_list':       JalurPenerimaan.objects.filter(status='aktif'),
        'gelombang_list':   GelombangPenerimaan.objects.all(),
        'status_choices':   Pendaftaran.STATUS_CHOICES,
        'filter_status':    status,
        'filter_jalur':     jalur,
        'filter_gelombang': gelombang,
        'filter_cari':      cari,
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
    # Tambahkan setelah query dokumen_list
    recruiter = None
    if pendaftaran.kode_referral:
        from afiliasi.models import Recruiter
        try:
            recruiter = Recruiter.objects.select_related('user').get(
                kode_referral=pendaftaran.kode_referral
            )
        except Recruiter.DoesNotExist:
            pass
   
    log_list = pendaftaran.log_status.all().order_by('-tgl_perubahan')

    context = {
        'pendaftaran': pendaftaran,
        'profil': profil,
        'dokumen_list': dokumen_list,
        'log_list': log_list,
        'recruiter': recruiter,
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
        status_baru = request.POST.get('status_baru')
        keterangan  = request.POST.get('keterangan', '')

        from pendaftaran.models import LogStatusPendaftaran
        LogStatusPendaftaran.objects.create(
            pendaftaran  = pendaftaran,
            status_lama  = pendaftaran.status,
            status_baru  = status_baru,
            keterangan   = keterangan,
            diubah_oleh  = request.user,
        )
        pendaftaran.status = status_baru
        pendaftaran.save()

        # Kirim notifikasi otomatis
        trigger_map = {
            'LULUS_ADM':     'dokumen_acc',
            'TERJADWAL':     'terjadwal',
            'LULUS_SELEKSI': 'lulus_seleksi',
            'TIDAK_LULUS':   'tidak_lulus',
            'DAFTAR_ULANG':  'daftar_ulang',
        }
        trigger = trigger_map.get(status_baru)
        if trigger:
            try:
                from notifikasi.engine import kirim_notifikasi
                kirim_notifikasi(trigger, pendaftaran)
            except Exception as e:
                logger.error(f'Error notifikasi: {e}')

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
        dok.status_verifikasi  = 'terverifikasi'
        dok.tgl_verifikasi     = timezone.now()
        dok.diverifikasi_oleh  = request.user
        dok.catatan_verifikasi = request.POST.get('catatan', '')
        dok.save()

        # Kirim notifikasi
        try:
            from notifikasi.engine import kirim_notifikasi
            kirim_notifikasi('dokumen_acc', dok.pendaftaran)
        except Exception as e:
            logger.error(f'Error notifikasi dokumen acc: {e}')

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

    from django.core.paginator import Paginator
    from django.db.models import Count, Q, Sum
    from pembayaran.models import KonfirmasiPembayaran

    status = request.GET.get('status', 'menunggu')
    q = (request.GET.get('q') or '').strip()

    qs = KonfirmasiPembayaran.objects.select_related(
        'tagihan',
        'tagihan__pendaftaran',
        'tagihan__pendaftaran__user',
        'tagihan__pendaftaran__jalur',
        'rekening_tujuan',
        'dikonfirmasi_oleh',
    ).order_by('-created_at')

    if status in ('menunggu', 'dikonfirmasi', 'ditolak'):
        qs = qs.filter(status=status)

    if q:
        qs = qs.filter(
            Q(tagihan__kode_bayar__icontains=q)
            | Q(tagihan__pendaftaran__no_pendaftaran__icontains=q)
            | Q(atas_nama_pengirim__icontains=q)
            | Q(no_transaksi__icontains=q)
        )

    stats = KonfirmasiPembayaran.objects.aggregate(
        total=Count('id'),
        menunggu=Count('id', filter=Q(status='menunggu')),
        dikonfirmasi=Count('id', filter=Q(status='dikonfirmasi')),
        ditolak=Count('id', filter=Q(status='ditolak')),
        total_diterima=Sum('jumlah_bayar', filter=Q(status='dikonfirmasi')),
    )

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_pmb/pembayaran.html', {
        'page_obj': page_obj,
        'status_active': status,
        'q': q,
        'stats': stats,
        'page_title': 'Verifikasi Pembayaran',
        **get_sidebar_counts()
    })

@login_required
def pembayaran_detail(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from pembayaran.models import KonfirmasiPembayaran

    konfirmasi = get_object_or_404(
        KonfirmasiPembayaran.objects.select_related(
            'tagihan',
            'tagihan__pendaftaran',
            'tagihan__pendaftaran__user',
            'tagihan__pendaftaran__jalur',
            'tagihan__pendaftaran__gelombang',
            'rekening_tujuan',
            'dikonfirmasi_oleh',
        ),
        pk=pk,
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        catatan = (request.POST.get('catatan_admin') or '').strip()

        if konfirmasi.status != 'menunggu':
            messages.warning(request, "Konfirmasi ini sudah diproses sebelumnya.")
            return redirect('admin_pmb:pembayaran_detail', pk=pk)

        tagihan = konfirmasi.tagihan

        if action == 'approve':
            konfirmasi.status = 'dikonfirmasi'
            konfirmasi.catatan_admin = catatan
            konfirmasi.dikonfirmasi_oleh = request.user
            konfirmasi.tgl_konfirmasi = timezone.now()
            konfirmasi.save()

            tagihan.status = 'lunas'
            tagihan.save(update_fields=['status', 'updated_at'])

            KonfirmasiPembayaran.objects.filter(
                tagihan=tagihan, status='menunggu',
            ).exclude(pk=konfirmasi.pk).update(
                status='ditolak',
                catatan_admin='Auto-rejected: konfirmasi lain sudah disetujui.',
                dikonfirmasi_oleh=request.user,
                tgl_konfirmasi=timezone.now(),
            )

            messages.success(
                request,
                f"Pembayaran {tagihan.kode_bayar} berhasil dikonfirmasi sebagai LUNAS."
            )
            # TODO Step 6: trigger notifikasi 'konfirmasi_pembayaran'
            return redirect('admin_pmb:pembayaran')

        elif action == 'reject':
            if not catatan:
                messages.error(request, "Catatan alasan penolakan wajib diisi.")
                return redirect('admin_pmb:pembayaran_detail', pk=pk)

            konfirmasi.status = 'ditolak'
            konfirmasi.catatan_admin = catatan
            konfirmasi.dikonfirmasi_oleh = request.user
            konfirmasi.tgl_konfirmasi = timezone.now()
            konfirmasi.save()

            has_other_active = tagihan.konfirmasi.filter(
                status__in=('menunggu', 'dikonfirmasi')
            ).exists()
            if not has_other_active:
                tagihan.status = 'belum_bayar'
                tagihan.save(update_fields=['status', 'updated_at'])

            messages.success(
                request,
                "Konfirmasi pembayaran ditolak. Maba bisa upload ulang bukti."
            )
            return redirect('admin_pmb:pembayaran')

    return render(request, 'admin_pmb/pembayaran_detail.html', {
        'konfirmasi': konfirmasi,
        'tagihan': konfirmasi.tagihan,
        'page_title': f'Verifikasi {konfirmasi.tagihan.kode_bayar}',
        **get_sidebar_counts()
    })

@login_required
def seleksi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from seleksi.models import JadwalSeleksi
    from master.models import JalurPenerimaan, GelombangPenerimaan

    jadwal_list = JadwalSeleksi.objects.select_related(
        'jalur', 'gelombang', 'dibuat_oleh'
    ).order_by('-tgl_seleksi')

    context = {
        'jadwal_list':    jadwal_list,
        'jalur_list':     JalurPenerimaan.objects.filter(status='aktif'),
        'gelombang_list': GelombangPenerimaan.objects.all(),
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/seleksi.html', context)

@login_required
def hasil(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from seleksi.models import HasilPenerimaan
    from pendaftaran.models import Pendaftaran
    from master.models import ProdiPMB, GelombangPenerimaan

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'input_hasil':
            pendaftaran_id = request.POST.get('pendaftaran_id')
            status_hasil   = request.POST.get('status_hasil')
            prodi_id       = request.POST.get('prodi_id')
            nilai_akhir    = request.POST.get('nilai_akhir') or None
            peringkat      = request.POST.get('peringkat') or None
            catatan        = request.POST.get('catatan', '')

            p = get_object_or_404(Pendaftaran, pk=pendaftaran_id)
            HasilPenerimaan.objects.update_or_create(
                pendaftaran=p,
                defaults={
                    'prodi_diterima_id': prodi_id,
                    'status':            status_hasil,
                    'nilai_akhir':       nilai_akhir,
                    'peringkat':         peringkat,
                    'catatan':           catatan,
                    'diinput_oleh':      request.user,
                }
            )
            if status_hasil == 'lulus':
                p.status = 'LULUS_SELEKSI'
            elif status_hasil == 'tidak_lulus':
                p.status = 'TIDAK_LULUS'
            p.save()
            messages.success(request, 'Hasil penerimaan berhasil disimpan.')
            return redirect('admin_pmb:hasil')

    gelombang_id = request.GET.get('gelombang', '')
    prodi_id     = request.GET.get('prodi', '')
    status_f     = request.GET.get('status', '')

    qs = Pendaftaran.objects.filter(
        status__in=['TERJADWAL', 'LULUS_ADM', 'LULUS_SELEKSI', 'TIDAK_LULUS']
    ).select_related('user', 'prodi_pilihan_1', 'gelombang', 'hasil')

    if gelombang_id: qs = qs.filter(gelombang_id=gelombang_id)
    if prodi_id:     qs = qs.filter(prodi_pilihan_1_id=prodi_id)
    if status_f:     qs = qs.filter(status=status_f)

    context = {
        'pendaftar_list':   qs,
        'prodi_list':       ProdiPMB.objects.filter(status='aktif'),
        'gelombang_list':   GelombangPenerimaan.objects.all(),
        'filter_gelombang': gelombang_id,
        'filter_prodi':     prodi_id,
        'filter_status':    status_f,
        'total_lulus':      Pendaftaran.objects.filter(status='LULUS_SELEKSI').count(),
        'total_tidak_lulus':Pendaftaran.objects.filter(status='TIDAK_LULUS').count(),
        'total_terjadwal':  Pendaftaran.objects.filter(status='TERJADWAL').count(),
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/hasil.html', context)

@login_required
def master(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from master.models import (JalurPenerimaan, GelombangPenerimaan,
                                ProdiPMB, PengaturanSistem)

    menu_master = [
        {'nama': 'Jalur Penerimaan',   'icon': '🚪', 'url': '/admin/master/jalurpenerimaan/',    'desc': 'Kelola jalur masuk'},
        {'nama': 'Gelombang',          'icon': '🌊', 'url': '/admin/master/gelombangpenerimaan/','desc': 'Jadwal & biaya gelombang'},
        {'nama': 'Program Studi',      'icon': '🎓', 'url': '/admin/master/prodipmb/',           'desc': 'Prodi yang dibuka PMB'},
        {'nama': 'Persyaratan Jalur',  'icon': '📋', 'url': '/admin/master/persyaratanjalur/',   'desc': 'Dokumen per jalur'},
        {'nama': 'Pengaturan Sistem',  'icon': '⚙️', 'url': '/admin/master/pengaturansistem/',  'desc': 'Konfigurasi umum PMB'},
        {'nama': 'Pengaturan Afiliasi','icon': '💰', 'url': '/admin/afiliasi/pengaturanafiliasi/','desc': 'Nominal komisi recruiter'},
    ]

    context = {
        'menu_master':    menu_master,
        'jalur_list':     JalurPenerimaan.objects.all().order_by('urutan'),
        'gelombang_list': GelombangPenerimaan.objects.all().order_by('-tgl_buka'),
        'prodi_list':     ProdiPMB.objects.filter(status='aktif').order_by('nama_prodi'),
        'pengaturan':     PengaturanSistem.get(),
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/master.html', context)

@login_required
def konten(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from konten.models import (Pengumuman, Testimoni, MitraKerjasama,
                                FAQ, BrosurFakultas, DokumenDownload)

    menu_konten = [
        {'nama': 'Pengumuman',      'icon': '📢', 'url': '/admin/konten/pengumuman/',    'desc': 'Kelola pengumuman PMB'},
        {'nama': 'Testimoni',       'icon': '💬', 'url': '/admin/konten/testimoni/',     'desc': 'Testimoni mahasiswa & alumni'},
        {'nama': 'Mitra Kerjasama', 'icon': '🤝', 'url': '/admin/konten/mitrakerjasama/','desc': 'Logo & link mitra kampus'},
        {'nama': 'FAQ',             'icon': '❓', 'url': '/admin/konten/faq/',           'desc': 'Pertanyaan yang sering ditanyakan'},
        {'nama': 'Brosur Fakultas', 'icon': '📄', 'url': '/admin/konten/brosurfakultas/','desc': 'Upload brosur per fakultas'},
        {'nama': 'Dokumen Download','icon': '📥', 'url': '/admin/konten/dokumendownload/','desc': 'Formulir & dokumen unduhan'},
        {'nama': 'Galeri Kampus',   'icon': '🖼️', 'url': '/admin/konten/galerikampus/', 'desc': 'Foto & video kampus'},
        {'nama': 'Media Sosial',    'icon': '📱', 'url': '/admin/konten/mediasosial/',  'desc': 'Link media sosial UNISAN'},
    ]

    context = {
        'menu_konten':      menu_konten,
        'total_pengumuman': Pengumuman.objects.filter(status='aktif').count(),
        'total_testimoni':  Testimoni.objects.filter(status='aktif').count(),
        'total_mitra':      MitraKerjasama.objects.filter(status='aktif').count(),
        'total_faq':        FAQ.objects.filter(status='aktif').count(),
        'total_brosur':     BrosurFakultas.objects.filter(status='aktif').count(),
        'total_dokumen':    DokumenDownload.objects.filter(status='aktif').count(),
        'pengumuman_list':  Pengumuman.objects.order_by('-tgl_tayang')[:5],
        'testimoni_list':   Testimoni.objects.order_by('-id')[:5],
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/konten.html', context)

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

    from pendaftaran.models import Pendaftaran, ProfilPendaftar
    from django.db.models import Count, Q

    # Statistik umum
    total_pendaftar = Pendaftaran.objects.count()
    total_lulus     = Pendaftaran.objects.filter(status='LULUS_SELEKSI').count()
    total_daftar_ulang = Pendaftaran.objects.filter(status='DAFTAR_ULANG').count()

    # Per prodi
    per_prodi = Pendaftaran.objects.values(
        'prodi_pilihan_1__nama_prodi'
    ).annotate(total=Count('id')).order_by('-total')

    # Per jalur
    per_jalur = Pendaftaran.objects.values(
        'jalur__nama_jalur'
    ).annotate(total=Count('id')).order_by('-total')

    # Per gelombang
    per_gelombang = Pendaftaran.objects.values(
        'gelombang__nama_gelombang'
    ).annotate(total=Count('id')).order_by('-total')

    # Per provinsi
    per_provinsi = ProfilPendaftar.objects.exclude(
        provinsi_nama=''
    ).values('provinsi_nama').annotate(
        total=Count('id')
    ).order_by('-total')[:15]

    # Per kab/kota
    per_kabkota = ProfilPendaftar.objects.exclude(
        kabupaten_kota_nama=''
    ).values('kabupaten_kota_nama', 'provinsi_nama').annotate(
        total=Count('id')
    ).order_by('-total')[:15]

    # Per asal sekolah
    per_sekolah = ProfilPendaftar.objects.exclude(
        asal_sekolah=''
    ).values('asal_sekolah', 'kabupaten_kota_nama').annotate(
        total=Count('id')
    ).order_by('-total')[:20]

 # Per sumber informasi (multi-select JSONField)
    per_sumber = ProfilPendaftar.objects.exclude(
        sumber_informasi=[]
    ).exclude(
        sumber_informasi__isnull=True
    ).values('sumber_informasi').annotate(
        total=Count('id')
    ).order_by('-total')


    # Ukuran baju
    per_ukuran = ProfilPendaftar.objects.exclude(
        ukuran_baju=''
    ).values('ukuran_baju').annotate(
        total=Count('id')
    ).order_by('ukuran_baju')

    # Per jenis kelamin
    per_gender = ProfilPendaftar.objects.values(
        'jenis_kelamin'
    ).annotate(total=Count('id')).order_by('jenis_kelamin')

    # Per agama
    per_agama = ProfilPendaftar.objects.exclude(
        agama_nama=''
    ).values('agama_nama').annotate(
        total=Count('id')
    ).order_by('-total')

    # Tren per bulan
    from django.db.models.functions import TruncMonth
    per_bulan = Pendaftaran.objects.annotate(
        bulan=TruncMonth('tgl_daftar')
    ).values('bulan').annotate(
        total=Count('id')
    ).order_by('bulan')

    tabs = [
        {'id': 'prodi',   'label': '📊 Prodi & Jalur'},
        {'id': 'wilayah', 'label': '🗺️ Wilayah'},
        {'id': 'sekolah', 'label': '🏫 Sekolah Asal'},
        {'id': 'sumber',  'label': '📣 Sumber Promosi'},
        {'id': 'baju',    'label': '👕 Ukuran Baju'},
        {'id': 'demo',    'label': '👥 Demografi'},
    ]

    context = {
        'total_pendaftar':    total_pendaftar,
        'total_lulus':        total_lulus,
        'total_daftar_ulang': total_daftar_ulang,
        'per_prodi':          per_prodi,
        'per_jalur':          per_jalur,
        'per_gelombang':      per_gelombang,
        'per_provinsi':       per_provinsi,
        'per_kabkota':        per_kabkota,
        'per_sekolah':        per_sekolah,
        'per_sumber':         per_sumber,
        'per_ukuran':         per_ukuran,
        'per_gender':         per_gender,
        'per_agama':          per_agama,
        'per_bulan':          per_bulan,
        'tabs':               tabs,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/laporan.html', context)

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

@login_required
def seleksi_tambah(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from seleksi.models import JadwalSeleksi
    from master.models import JalurPenerimaan, GelombangPenerimaan

    if request.method == 'POST':
        JadwalSeleksi.objects.create(
            jalur         = JalurPenerimaan.objects.get(pk=request.POST['jalur']),
            gelombang     = GelombangPenerimaan.objects.get(pk=request.POST['gelombang']),
            jenis_seleksi = request.POST['jenis_seleksi'],
            nama_seleksi  = request.POST['nama_seleksi'],
            tgl_seleksi   = request.POST['tgl_seleksi'],
            jam_mulai     = request.POST['jam_mulai'],
            jam_selesai   = request.POST['jam_selesai'],
            lokasi        = request.POST.get('lokasi', ''),
            link_online   = request.POST.get('link_online', ''),
            keterangan    = request.POST.get('keterangan', ''),
            status        = 'draft',
            dibuat_oleh   = request.user,
        )
        messages.success(request, 'Jadwal seleksi berhasil ditambahkan!')
        return redirect('admin_pmb:seleksi')

    from seleksi.models import JadwalSeleksi as JS
    context = {
        'jalur_list':     JalurPenerimaan.objects.filter(status='aktif'),
        'gelombang_list': GelombangPenerimaan.objects.all(),
        'jenis_choices':  JS.JENIS_CHOICES,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/seleksi_tambah.html', context)


@login_required
def seleksi_detail(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from seleksi.models import JadwalSeleksi, PesertaSeleksi
    from pendaftaran.models import Pendaftaran

    jadwal = get_object_or_404(JadwalSeleksi, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'publish':
            pendaftar = Pendaftaran.objects.filter(
                jalur=jadwal.jalur,
                gelombang=jadwal.gelombang,
                status__in=['LENGKAP', 'LULUS_ADM', 'TERJADWAL']
            )
            added = 0
            for p in pendaftar:
                obj, created = PesertaSeleksi.objects.get_or_create(
                    jadwal=jadwal, pendaftaran=p,
                    defaults={'no_ujian': f'{jadwal.pk:03d}{p.pk:04d}'}
                )
                if created:
                    added += 1
                    p.status = 'TERJADWAL'
                    p.save()
            jadwal.status = 'publish'
            jadwal.save()
            messages.success(request, f'Jadwal dipublikasi! {added} peserta ditambahkan.')

        elif action == 'nilai':
            peserta_id = request.POST.get('peserta_id')
            nilai      = request.POST.get('nilai')
            hadir      = request.POST.get('hadir')
            catatan    = request.POST.get('catatan', '')
            from django.utils import timezone
            PesertaSeleksi.objects.filter(pk=peserta_id).update(
                nilai            = nilai if nilai else None,
                status_kehadiran = hadir,
                catatan_penilai  = catatan,
                dinilai_oleh     = request.user,
                tgl_penilaian    = timezone.now(),
            )
            messages.success(request, 'Nilai berhasil disimpan.')

        elif action == 'selesai':
            jadwal.status = 'selesai'
            jadwal.save()
            messages.success(request, 'Jadwal seleksi ditandai selesai.')

        return redirect('admin_pmb:seleksi_detail', pk=pk)

    peserta_list = jadwal.peserta.select_related(
        'pendaftaran__user', 'pendaftaran__prodi_pilihan_1'
    ).order_by('no_ujian')

    context = {
        'jadwal':       jadwal,
        'peserta_list': peserta_list,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/seleksi_detail.html', context)

@login_required
def export_pendaftar(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse
    from pendaftaran.models import Pendaftaran, ProfilPendaftar

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Data Pendaftar'

    # Style
    header_font  = Font(bold=True, color='FFFFFF', size=11)
    header_fill  = PatternFill(fill_type='solid', fgColor='667EEA')
    center       = Alignment(horizontal='center', vertical='center')
    thin         = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Header
    headers = [
        'No', 'No. Pendaftaran', 'Nama Lengkap', 'Email', 'No HP',
        'Jalur', 'Gelombang', 'Prodi Pilihan 1', 'Prodi Pilihan 2',
        'Status', 'Tgl Daftar',
        'NIK', 'Tempat Lahir', 'Tgl Lahir', 'Jenis Kelamin', 'Agama',
        'Alamat', 'Provinsi', 'Kab/Kota', 'Kecamatan', 'Kode Pos',
        'Nama Ayah', 'Pekerjaan Ayah', 'Nama Ibu', 'Pekerjaan Ibu', 'No HP Ortu',
        'Asal Sekolah', 'Jurusan Sekolah', 'Tahun Lulus', 'Nilai Rata-rata',
        'Ukuran Baju', 'Sumber Informasi', 'Kode Referral',
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center
        cell.border    = thin

    # Lebar kolom
    col_widths = [5,20,25,30,15,12,15,25,25,15,15,
                  18,15,12,12,12,35,20,20,20,10,
                  25,20,25,20,15,
                  35,20,12,8,
                  10,20,15]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = width

    # Freeze header
    ws.freeze_panes = 'A2'

    # Data
    pendaftar_list = Pendaftaran.objects.select_related(
        'user', 'jalur', 'gelombang', 'prodi_pilihan_1', 'prodi_pilihan_2'
    ).order_by('tgl_daftar')

    for row_num, p in enumerate(pendaftar_list, 2):
        try:
            profil = p.profil
        except:
            profil = None

        data = [
            row_num - 1,
            p.no_pendaftaran,
            p.user.get_full_name(),
            p.user.email,
            p.user.no_hp,
            p.jalur.nama_jalur,
            p.gelombang.nama_gelombang,
            p.prodi_pilihan_1.nama_prodi if p.prodi_pilihan_1 else '',
            p.prodi_pilihan_2.nama_prodi if p.prodi_pilihan_2 else '',
            p.get_status_display(),
            p.tgl_daftar.strftime('%d/%m/%Y') if p.tgl_daftar else '',
            profil.nik if profil else '',
            profil.tempat_lahir if profil else '',
            profil.tgl_lahir.strftime('%d/%m/%Y') if profil and profil.tgl_lahir else '',
            profil.get_jenis_kelamin_display() if profil and profil.jenis_kelamin else '',
            profil.agama_nama if profil else '',
            profil.alamat_lengkap if profil else '',
            profil.provinsi_nama if profil else '',
            profil.kabupaten_kota_nama if profil else '',
            profil.kecamatan_nama if profil else '',
            profil.kode_pos if profil else '',
            profil.nama_ayah if profil else '',
            profil.pekerjaan_ayah if profil else '',
            profil.nama_ibu if profil else '',
            profil.pekerjaan_ibu if profil else '',
            profil.no_hp_ortu if profil else '',
            profil.asal_sekolah if profil else '',
            profil.jurusan_sekolah if profil else '',
            profil.tahun_lulus if profil else '',
            str(profil.nilai_rata_rata) if profil and profil.nilai_rata_rata else '',
            profil.ukuran_baju if profil else '',
            ', '.join([dict(ProfilPendaftar.SUMBER_INFO_CHOICES).get(s, s) for s in (profil.sumber_informasi or [])]) if profil else '',
           
            p.kode_referral or '',
        ]

        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.border    = thin
            cell.alignment = Alignment(vertical='center')
            if row_num % 2 == 0:
                cell.fill = PatternFill(fill_type='solid', fgColor='F8F9FF')

    # Auto filter
    ws.auto_filter.ref = f'A1:{ws.cell(1, len(headers)).column_letter}1'

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="data_pendaftar_pmb.xlsx"'
    wb.save(response)
    return response


@login_required
def export_ukuran_baju(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse
    from django.db.models import Count
    from pendaftaran.models import ProfilPendaftar, Pendaftaran

    wb = openpyxl.Workbook()

    # Sheet 1 — Detail per pendaftar
    ws1 = wb.active
    ws1.title = 'Detail Ukuran Baju'

    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill(fill_type='solid', fgColor='667EEA')
    thin = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    headers1 = ['No', 'No. Pendaftaran', 'Nama', 'Prodi', 'Jalur', 'Ukuran Baju']
    for col, h in enumerate(headers1, 1):
        cell = ws1.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin

    ws1.column_dimensions['A'].width = 5
    ws1.column_dimensions['B'].width = 22
    ws1.column_dimensions['C'].width = 28
    ws1.column_dimensions['D'].width = 25
    ws1.column_dimensions['E'].width = 15
    ws1.column_dimensions['F'].width = 12
    ws1.freeze_panes = 'A2'

    profil_list = ProfilPendaftar.objects.exclude(
        ukuran_baju=''
    ).select_related(
        'pendaftaran__user',
        'pendaftaran__prodi_pilihan_1',
        'pendaftaran__jalur'
    ).order_by('ukuran_baju', 'pendaftaran__prodi_pilihan_1__nama_prodi')

    for i, pr in enumerate(profil_list, 2):
        data = [
            i - 1,
            pr.pendaftaran.no_pendaftaran,
            pr.pendaftaran.user.get_full_name(),
            pr.pendaftaran.prodi_pilihan_1.nama_prodi if pr.pendaftaran.prodi_pilihan_1 else '',
            pr.pendaftaran.jalur.nama_jalur,
            pr.ukuran_baju,
        ]
        for col, val in enumerate(data, 1):
            cell = ws1.cell(row=i, column=col, value=val)
            cell.border = thin
            if i % 2 == 0:
                cell.fill = PatternFill(fill_type='solid', fgColor='F8F9FF')

    # Sheet 2 — Rekap per ukuran
    ws2 = wb.create_sheet('Rekap Ukuran')
    headers2 = ['Ukuran', 'Jumlah', 'Persentase']
    for col, h in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin

    ws2.column_dimensions['A'].width = 12
    ws2.column_dimensions['B'].width = 12
    ws2.column_dimensions['C'].width = 15

    rekap = ProfilPendaftar.objects.exclude(
        ukuran_baju=''
    ).values('ukuran_baju').annotate(
        total=Count('id')
    ).order_by('ukuran_baju')

    total_all = sum(r['total'] for r in rekap)

    for i, r in enumerate(rekap, 2):
        pct = f"{(r['total']/total_all*100):.1f}%" if total_all else '0%'
        for col, val in enumerate([r['ukuran_baju'], r['total'], pct], 1):
            cell = ws2.cell(row=i, column=col, value=val)
            cell.border = thin
            cell.alignment = Alignment(horizontal='center')

    # Total
    total_row = len(list(rekap)) + 2
    ws2.cell(total_row, 1, 'TOTAL').font = Font(bold=True)
    ws2.cell(total_row, 2, total_all).font = Font(bold=True)
    ws2.cell(total_row, 3, '100%').font = Font(bold=True)

    # Sheet 3 — Rekap per prodi per ukuran
    ws3 = wb.create_sheet('Per Prodi')
    ws3.cell(1, 1, 'Prodi').font = header_font
    ws3.cell(1, 1).fill = header_fill

    ukuran_list = ['S', 'M', 'L', 'XL', 'XXL', '3XL']
    for col, uk in enumerate(ukuran_list, 2):
        cell = ws3.cell(1, col, uk)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    ws3.cell(1, len(ukuran_list)+2, 'Total').font = header_font
    ws3.cell(1, len(ukuran_list)+2).fill = header_fill

    from master.models import ProdiPMB
    prodi_list = ProdiPMB.objects.filter(status='aktif').order_by('nama_prodi')

    for row, prodi in enumerate(prodi_list, 2):
        ws3.cell(row, 1, prodi.nama_prodi)
        total_prodi = 0
        for col, uk in enumerate(ukuran_list, 2):
            jumlah = ProfilPendaftar.objects.filter(
                ukuran_baju=uk,
                pendaftaran__prodi_pilihan_1=prodi
            ).count()
            ws3.cell(row, col, jumlah).alignment = Alignment(horizontal='center')
            total_prodi += jumlah
        ws3.cell(row, len(ukuran_list)+2, total_prodi).font = Font(bold=True)

    ws3.column_dimensions['A'].width = 30

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="rekap_ukuran_baju.xlsx"'
    wb.save(response)
    return response


@login_required
def export_wilayah(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse
    from django.db.models import Count
    from pendaftaran.models import ProfilPendaftar

    wb  = openpyxl.Workbook()
    hf  = Font(bold=True, color='FFFFFF')
    hfi = PatternFill(fill_type='solid', fgColor='667EEA')
    th  = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    def set_header(ws, headers, widths):
        for col, h in enumerate(headers, 1):
            c = ws.cell(1, col, h)
            c.font = hf; c.fill = hfi
            c.alignment = Alignment(horizontal='center')
            c.border = th
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(1,i).column_letter].width = w
        ws.freeze_panes = 'A2'

    # Sheet 1 — Per Provinsi
    ws1 = wb.active
    ws1.title = 'Per Provinsi'
    set_header(ws1, ['No','Provinsi','Jumlah Pendaftar','%'], [5,30,20,10])
    per_prov = ProfilPendaftar.objects.exclude(provinsi_nama='').values(
        'provinsi_nama').annotate(total=Count('id')).order_by('-total')
    total = sum(p['total'] for p in per_prov)
    for i, p in enumerate(per_prov, 2):
        pct = f"{p['total']/total*100:.1f}%" if total else '0%'
        for col, val in enumerate([i-1, p['provinsi_nama'], p['total'], pct], 1):
            c = ws1.cell(i, col, val); c.border = th
            if i%2==0: c.fill = PatternFill(fill_type='solid', fgColor='F8F9FF')

    # Sheet 2 — Per Kab/Kota
    ws2 = wb.create_sheet('Per Kab-Kota')
    set_header(ws2, ['No','Provinsi','Kab/Kota','Jumlah','%'], [5,25,25,15,10])
    per_kab = ProfilPendaftar.objects.exclude(kabupaten_kota_nama='').values(
        'provinsi_nama','kabupaten_kota_nama').annotate(
        total=Count('id')).order_by('-total')
    total2 = sum(p['total'] for p in per_kab)
    for i, p in enumerate(per_kab, 2):
        pct = f"{p['total']/total2*100:.1f}%" if total2 else '0%'
        for col, val in enumerate([i-1, p['provinsi_nama'],
                                   p['kabupaten_kota_nama'], p['total'], pct], 1):
            c = ws2.cell(i, col, val); c.border = th
            if i%2==0: c.fill = PatternFill(fill_type='solid', fgColor='F8F9FF')

    # Sheet 3 — Per Sekolah
    ws3 = wb.create_sheet('Per Sekolah')
    set_header(ws3, ['No','Asal Sekolah','Kab/Kota','Jumlah Pendaftar'], [5,40,25,18])
    per_skl = ProfilPendaftar.objects.exclude(asal_sekolah='').values(
        'asal_sekolah','kabupaten_kota_nama').annotate(
        total=Count('id')).order_by('-total')
    for i, p in enumerate(per_skl, 2):
        for col, val in enumerate([i-1, p['asal_sekolah'],
                                   p['kabupaten_kota_nama'], p['total']], 1):
            c = ws3.cell(i, col, val); c.border = th
            if i%2==0: c.fill = PatternFill(fill_type='solid', fgColor='F8F9FF')

    # Sheet 4 — Sumber Informasi
    ws4 = wb.create_sheet('Sumber Informasi')
    set_header(ws4, ['No','Sumber Informasi','Jumlah','%'], [5,30,15,10])

    # Per sumber informasi (multi-select JSONField)
    from collections import Counter
    all_sumber = []
    for profil in ProfilPendaftar.objects.exclude(sumber_informasi=[]).exclude(sumber_informasi__isnull=True):
        if isinstance(profil.sumber_informasi, list):
            all_sumber.extend(profil.sumber_informasi)
    counter = Counter(all_sumber)
    total4 = sum(counter.values())
    sumber_map = dict(ProfilPendaftar.SUMBER_INFO_CHOICES)
    for i, (kode, total) in enumerate(counter.most_common(), 2):
        pct = f"{total/total4*100:.1f}%" if total4 else '0%'
        label = sumber_map.get(kode, kode)
        for col, val in enumerate([i-1, label, total, pct], 1):
            c = ws4.cell(i, col, val); c.border = th
            if i%2==0: c.fill = PatternFill(fill_type='solid', fgColor='F8F9FF')


    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="rekap_wilayah_pmb.xlsx"'
    wb.save(response)
    return response

@login_required
def notifikasi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from notifikasi.models import TemplateNotifikasi, LogNotifikasi

    template_list = TemplateNotifikasi.objects.all().order_by('trigger')
    log_terbaru   = LogNotifikasi.objects.select_related(
        'user', 'template'
    ).order_by('-tgl_kirim')[:20]

    context = {
        'template_list': template_list,
        'log_terbaru':   log_terbaru,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/notifikasi.html', context)


@login_required
def notifikasi_kirim(request):
    """Kirim notifikasi massal manual"""
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    if request.method == 'POST':
        status_target = request.POST.get('status_target', '')
        subjek        = request.POST.get('subjek', '')
        isi_email     = request.POST.get('isi_email', '')
        isi_wa        = request.POST.get('isi_wa', '')
        kirim_ke      = request.POST.get('kirim_ke', 'both')

        qs = Pendaftaran.objects.select_related('user', 'jalur', 'prodi_pilihan_1')
        if status_target:
            qs = qs.filter(status=status_target)

        from notifikasi.engine import kirim_notifikasi_manual
        berhasil, gagal = kirim_notifikasi_manual(
            list(qs), subjek, isi_email, isi_wa, kirim_ke
        )
        messages.success(
            request,
            f'Notifikasi terkirim: {berhasil} berhasil, {gagal} gagal dari {qs.count()} target.'
        )

    return redirect('admin_pmb:notifikasi')



@login_required
def notifikasi(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from notifikasi.models import TemplateNotifikasi, LogNotifikasi

    template_list = TemplateNotifikasi.objects.all().order_by('trigger')
    log_terbaru   = LogNotifikasi.objects.select_related(
        'user', 'template'
    ).order_by('-tgl_kirim')[:20]

    variabel_list = [
        'nama', 'no_pendaftaran', 'jalur', 'gelombang',
        'prodi', 'status', 'email', 'no_hp',
        'url_dashboard', 'nama_kampus', 'kontak_pmb',
    ]

    context = {
        'template_list':  template_list,
        'log_terbaru':    log_terbaru,
        'variabel_list':  variabel_list,
        'status_choices': Pendaftaran.STATUS_CHOICES,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/notifikasi.html', context)

@login_required
def notifikasi_log(request):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from notifikasi.models import LogNotifikasi
    from django.db.models import Count
    from django.utils.dateparse import parse_date

    # Handle hapus
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'hapus':
            hapus_filter = request.POST.get('hapus_filter', '0')

            if hapus_filter == '1':
                # Hapus berdasarkan filter
                qs = LogNotifikasi.objects.all()
                dari   = request.POST.get('filter_dari', '')
                sampai = request.POST.get('filter_sampai', '')
                status = request.POST.get('filter_status', '')
                jenis  = request.POST.get('filter_jenis', '')
                if dari:    qs = qs.filter(tgl_kirim__date__gte=dari)
                if sampai:  qs = qs.filter(tgl_kirim__date__lte=sampai)
                if status:  qs = qs.filter(status=status)
                if jenis:   qs = qs.filter(jenis=jenis)
                jumlah = qs.count()
                qs.delete()
                messages.success(request, f'{jumlah} log berhasil dihapus.')
            else:
                # Hapus yang dicentang
                log_ids = request.POST.getlist('log_ids')
                if log_ids:
                    jumlah = LogNotifikasi.objects.filter(pk__in=log_ids).count()
                    LogNotifikasi.objects.filter(pk__in=log_ids).delete()
                    messages.success(request, f'{jumlah} log berhasil dihapus.')

        return redirect('admin_pmb:notifikasi_log')

    # Filter
    filter_dari   = request.GET.get('dari', '')
    filter_sampai = request.GET.get('sampai', '')
    filter_status = request.GET.get('status', '')
    filter_jenis  = request.GET.get('jenis', '')

    qs = LogNotifikasi.objects.select_related(
        'user', 'template', 'pendaftaran'
    ).order_by('-tgl_kirim')

    if filter_dari:   qs = qs.filter(tgl_kirim__date__gte=filter_dari)
    if filter_sampai: qs = qs.filter(tgl_kirim__date__lte=filter_sampai)
    if filter_status: qs = qs.filter(status=filter_status)
    if filter_jenis:  qs = qs.filter(jenis=filter_jenis)

    stat = LogNotifikasi.objects.values('status').annotate(total=Count('id'))

    context = {
        'log_list':      qs[:200],
        'stat':          stat,
        'filter_dari':   filter_dari,
        'filter_sampai': filter_sampai,
        'filter_status': filter_status,
        'filter_jenis':  filter_jenis,
        **get_sidebar_counts(),
    }
    return render(request, 'admin_pmb/notifikasi_log.html', context)

@login_required
def cetak_kartu(request, pk):
    """Cetak kartu peserta satu pendaftar"""
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from django.http import HttpResponse
    from seleksi.kartu_pdf import buat_kartu_peserta
    from seleksi.models import KartuPeserta

    pendaftaran = get_object_or_404(Pendaftaran, pk=pk)

    # Generate atau ambil nomor kartu
    kartu, created = KartuPeserta.objects.get_or_create(
        pendaftaran=pendaftaran,
        defaults={
            'no_kartu': f'PMB-{pendaftaran.gelombang.kode_gelombang}-{pendaftaran.pk:04d}'
                        if hasattr(pendaftaran.gelombang, 'kode_gelombang')
                        else f'PMB-{pendaftaran.no_pendaftaran}',
        }
    )
    kartu.sudah_cetak = True
    kartu.save()

    # Ambil jadwal terbaru jika ada
    jadwal = None
    try:
        from seleksi.models import PesertaSeleksi
        peserta = PesertaSeleksi.objects.filter(
            pendaftaran=pendaftaran
        ).select_related('jadwal').last()
        if peserta:
            jadwal = peserta.jadwal
    except:
        pass

    buffer = buat_kartu_peserta(pendaftaran, jadwal)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="kartu_{pendaftaran.no_pendaftaran}.pdf"'
    )
    return response


@login_required
def cetak_kartu_massal(request):
    """Cetak kartu peserta massal berdasarkan filter"""
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from django.http import HttpResponse
    from seleksi.kartu_pdf import buat_kartu_peserta
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO

    gelombang_id = request.GET.get('gelombang', '')
    jalur_id     = request.GET.get('jalur', '')
    status       = request.GET.get('status', 'LULUS_ADM')

    qs = Pendaftaran.objects.select_related(
        'user', 'jalur', 'gelombang', 'prodi_pilihan_1'
    )
    if gelombang_id: qs = qs.filter(gelombang_id=gelombang_id)
    if jalur_id:     qs = qs.filter(jalur_id=jalur_id)
    if status:       qs = qs.filter(status=status)

    if not qs.exists():
        messages.warning(request, 'Tidak ada pendaftar yang sesuai filter.')
        return redirect('admin_pmb:pendaftar')

    # Gabungkan semua PDF
    from PyPDF2 import PdfMerger
    merger = PdfMerger()

    for p in qs:
        try:
            buf = buat_kartu_peserta(p)
            merger.append(buf)
            from seleksi.models import KartuPeserta
            KartuPeserta.objects.get_or_create(
                pendaftaran=p,
                defaults={'no_kartu': f'PMB-{p.no_pendaftaran}'}
            )
        except Exception as e:
            logger.error(f'Error cetak kartu {p.no_pendaftaran}: {e}')

    output = BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="kartu_peserta_massal.pdf"'
    return response

@login_required
def cetak_formulir_admin(request, pk):
    if not cek_admin(request.user):
        return redirect('dashboard:index')

    from django.http import HttpResponse
    from seleksi.kartu_pdf import buat_formulir_pendaftaran

    pendaftaran = get_object_or_404(
        Pendaftaran.objects.select_related(
            'user', 'jalur', 'gelombang',
            'prodi_pilihan_1', 'prodi_pilihan_2'
        ), pk=pk
    )

    buffer = buat_formulir_pendaftaran(pendaftaran)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="formulir_{pendaftaran.no_pendaftaran}.pdf"'
    )
    return response