from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


@login_required
def index(request):
    user = request.user

    if user.role in ['admin_pmb', 'operator_pmb', 'panitia_seleksi', 'pimpinan']:
        return redirect('dashboard:admin')
    elif user.role == 'recruiter':
        return redirect('dashboard:recruiter')
    else:
        return redirect('dashboard:calon_maba')


@login_required
def calon_maba(request):
    from master.models import PengaturanSistem
    from pendaftaran.models import Pendaftaran, ProfilPendaftar

    # Kalau recruiter nyasar ke sini, redirect ke dashboard recruiter
    if request.user.role == 'recruiter':
        return redirect('afiliasi:dashboard')

    user       = request.user
    pengaturan = PengaturanSistem.get()

    # Ambil data pendaftaran
    try:
        pendaftaran = Pendaftaran.objects.get(user=user)
        profil      = pendaftaran.profil
    except Pendaftaran.DoesNotExist:
        pendaftaran = None
        profil      = None

    context = {
        'user':        user,
        'pengaturan':  pengaturan,
        'pendaftaran': pendaftaran,
        'profil':      profil,
    }
    return render(request, 'dashboard/calon_maba.html', context)


@login_required
def admin_pmb(request):
    from master.models import PengaturanSistem
    from pendaftaran.models import Pendaftaran

    if request.user.role not in ['admin_pmb', 'operator_pmb', 'panitia_seleksi', 'pimpinan']:
        return redirect('dashboard:calon_maba')

    pengaturan   = PengaturanSistem.get()
    total        = Pendaftaran.objects.count()
    draft        = Pendaftaran.objects.filter(status='DRAFT').count()
    diverifikasi = Pendaftaran.objects.filter(status='DIVERIFIKASI').count()
    lulus        = Pendaftaran.objects.filter(status='LULUS_SELEKSI').count()
    daftar_ulang = Pendaftaran.objects.filter(status='DAFTAR_ULANG').count()
    terbaru      = Pendaftaran.objects.select_related('user', 'jalur', 'prodi_pilihan_1').order_by('-tgl_daftar')[:10]

    context = {
        'user':        request.user,
        'pengaturan':  pengaturan,
        'total':       total,
        'draft':       draft,
        'diverifikasi':diverifikasi,
        'lulus':       lulus,
        'daftar_ulang':daftar_ulang,
        'terbaru':     terbaru,
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def recruiter_dashboard(request):
    if request.user.role != 'recruiter':
        return redirect('dashboard:index')

    from master.models import PengaturanSistem
    pengaturan = PengaturanSistem.get()

    context = {
        'user':       request.user,
        'pengaturan': pengaturan,
    }
    return render(request, 'dashboard/recruiter.html', context)

@login_required
def admin_pmb(request):
    return redirect('admin_pmb:dashboard')

@login_required
def index(request):
    user = request.user
    
    # Recruiter → redirect ke dashboard recruiter
    if user.role == 'recruiter':
        return redirect('afiliasi:dashboard')
    
    # Admin → redirect ke admin PMB
    if user.role in ['admin_pmb', 'operator_pmb', 'panitia_seleksi', 'pimpinan']:
        return redirect('admin_pmb:dashboard')
    
    # Calon maba → dashboard maba
    return redirect('dashboard:calon_maba')