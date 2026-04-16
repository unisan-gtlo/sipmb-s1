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
            form.save()
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