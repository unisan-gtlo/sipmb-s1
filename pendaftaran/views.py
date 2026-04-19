import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Pendaftaran, ProfilPendaftar
from .forms import ProfilDiriForm, ProfilOrtuForm, ProfilPendidikanForm, ProfilFotoForm

logger = logging.getLogger(__name__)


def _get_pendaftaran(user):
    """Helper ambil pendaftaran user, return None jika tidak ada"""
    try:
        return Pendaftaran.objects.get(user=user)
    except Pendaftaran.DoesNotExist:
        return None


@login_required
def profil_diri(request):
    pendaftaran = _get_pendaftaran(request.user)
    if not pendaftaran:
        messages.warning(request, 'Anda belum memiliki data pendaftaran.')
        return redirect('dashboard:index')
    profil, _ = ProfilPendaftar.objects.get_or_create(pendaftaran=pendaftaran)
    if request.method == 'POST':
        form = ProfilDiriForm(request.POST, instance=profil)
        if form.is_valid():
            # Sync nama_lengkap ke User (first_name + last_name)
            nama_baru = form.cleaned_data.get('nama_lengkap', '').strip()
            if nama_baru and nama_baru != request.user.nama_lengkap:
                # Split nama: kata pertama = first_name, sisanya = last_name
                parts = nama_baru.split(' ', 1)
                request.user.first_name = parts[0]
                request.user.last_name = parts[1] if len(parts) > 1 else ''
                request.user.save(update_fields=['first_name', 'last_name'])
            
            form.save()
            messages.success(request, 'Data diri berhasil disimpan.')
            return redirect('pendaftaran:profil_ortu')
    else:
        form = ProfilDiriForm(instance=profil)

    return render(request, 'pendaftaran/profil_diri.html', {
        'form':        form,
        'pendaftaran': pendaftaran,
        'profil':      profil,
        'tab_aktif':   'diri',
    })

@login_required
def profil_ortu(request):
    pendaftaran = _get_pendaftaran(request.user)
    if not pendaftaran:
        return redirect('dashboard:index')
    profil, _ = ProfilPendaftar.objects.get_or_create(pendaftaran=pendaftaran)
    if request.method == 'POST':
        form = ProfilOrtuForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data orang tua berhasil disimpan.')
            return redirect('pendaftaran:profil_pendidikan')
    else:
        form = ProfilOrtuForm(instance=profil)
    return render(request, 'pendaftaran/profil_ortu.html', {
        'form':        form,
        'pendaftaran': pendaftaran,
        'profil':      profil,
        'tab_aktif':   'ortu',
    })

@login_required
def profil_pendidikan(request):
    pendaftaran = _get_pendaftaran(request.user)
    if not pendaftaran:
        return redirect('dashboard:index')

    profil, _ = ProfilPendaftar.objects.get_or_create(pendaftaran=pendaftaran)

    if request.method == 'POST':
        form = ProfilPendidikanForm(request.POST, instance=profil)
        if form.is_valid():
            # Handle jurusan_manual kalau pilih "Lainnya"
            jurusan_id = form.cleaned_data.get('jurusan_id', '')
            jurusan_manual = form.cleaned_data.get('jurusan_manual', '').strip()
            
            instance = form.save(commit=False)
            
            # Kalau "lainnya" dipilih, override jurusan_sekolah dengan teks manual
            if jurusan_id == 'lainnya' and jurusan_manual:
                instance.jurusan_sekolah = jurusan_manual
            elif jurusan_id:
                # Ambil label dari JURUSAN_CHOICES
                jurusan_dict = dict(ProfilPendaftar.JURUSAN_CHOICES)
                instance.jurusan_sekolah = jurusan_dict.get(jurusan_id, jurusan_id)
            
            instance.save()
            messages.success(request, 'Data pendidikan berhasil disimpan.')
            return redirect('pendaftaran:profil_foto')
    else:
        form = ProfilPendidikanForm(instance=profil)

    return render(request, 'pendaftaran/profil_pendidikan.html', {
        'form':        form,
        'pendaftaran': pendaftaran,
        'profil':      profil,
        'tab_aktif':   'pendidikan',
    })


@login_required
def profil_foto(request):
    pendaftaran = _get_pendaftaran(request.user)
    if not pendaftaran:
        return redirect('dashboard:index')

    profil, _ = ProfilPendaftar.objects.get_or_create(pendaftaran=pendaftaran)

    if request.method == 'POST':
        form = ProfilFotoForm(request.POST, request.FILES, instance=profil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto berhasil diunggah.')
            return redirect('dashboard:calon_maba')
    else:
        form = ProfilFotoForm(instance=profil)

    return render(request, 'pendaftaran/profil_foto.html', {
        'form':        form,
        'pendaftaran': pendaftaran,
        'profil':      profil,
        'tab_aktif':   'foto',
    })

@login_required
def cetak_kartu_maba(request):
    from seleksi.models import KartuPeserta, PesertaSeleksi
    from seleksi.kartu_pdf import buat_kartu_peserta
    from django.http import HttpResponse
    from django.contrib import messages

    # Ambil pendaftaran user yang login
    try:
        pendaftaran = Pendaftaran.objects.filter(
            user=request.user
        ).select_related(
            'jalur', 'gelombang', 'prodi_pilihan_1'
        ).first()

        if not pendaftaran:
            messages.error(request, 'Data pendaftaran tidak ditemukan.')
            return redirect('dashboard:calon_maba')

    except Exception as e:
        messages.error(request, f'Error: {e}')
        return redirect('dashboard:calon_maba')

    # Cek status
    status_boleh_cetak = ['LULUS_ADM', 'TERJADWAL', 'LULUS_SELEKSI', 'DAFTAR_ULANG']
    if pendaftaran.status not in status_boleh_cetak:
        messages.warning(request,
            'Kartu peserta belum tersedia. '
            'Kartu dapat dicetak setelah dokumen diverifikasi panitia PMB.')
        return redirect('dashboard:calon_maba')

    # Generate kartu
    kartu, _ = KartuPeserta.objects.get_or_create(
        pendaftaran=pendaftaran,
        defaults={'no_kartu': f'PMB-{pendaftaran.no_pendaftaran}'}
    )
    kartu.sudah_cetak = True
    kartu.save()

    # Ambil jadwal jika ada
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
def cetak_formulir(request):
    from seleksi.kartu_pdf import buat_formulir_pendaftaran
    from django.http import HttpResponse

    pendaftaran = Pendaftaran.objects.filter(
        user=request.user
    ).select_related(
        'jalur', 'gelombang', 'prodi_pilihan_1', 'prodi_pilihan_2'
    ).first()

    if not pendaftaran:
        from django.contrib import messages
        messages.error(request, 'Data pendaftaran tidak ditemukan.')
        return redirect('dashboard:calon_maba')

    buffer = buat_formulir_pendaftaran(pendaftaran)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="formulir_{pendaftaran.no_pendaftaran}.pdf"'
    )
    return response