import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import DokumenPendaftar
from .forms import UploadDokumenForm
from pendaftaran.models import Pendaftaran
from master.models import PersyaratanJalur

logger = logging.getLogger(__name__)


@login_required
def daftar_dokumen(request):
    """Halaman daftar semua dokumen persyaratan"""
    try:
        pendaftaran = Pendaftaran.objects.get(user=request.user)
    except Pendaftaran.DoesNotExist:
        messages.warning(request, 'Anda belum memiliki data pendaftaran.')
        return redirect('dashboard:index')

    # Ambil persyaratan berdasarkan jalur
    persyaratan_list = PersyaratanJalur.objects.filter(
        jalur=pendaftaran.jalur
    ).order_by('urutan')

    # Buat atau ambil dokumen per persyaratan
    dokumen_list = []
    for syarat in persyaratan_list:
        dokumen, _ = DokumenPendaftar.objects.get_or_create(
            pendaftaran=pendaftaran,
            persyaratan=syarat
        )
        dokumen_list.append(dokumen)

    # Hitung progress
    total   = len(dokumen_list)
    uploaded = sum(1 for d in dokumen_list if d.sudah_upload)
    verified = sum(1 for d in dokumen_list if d.status_verifikasi == 'terverifikasi')
    pct      = int((uploaded / total * 100)) if total > 0 else 0

    context = {
        'pendaftaran':  pendaftaran,
        'dokumen_list': dokumen_list,
        'total':        total,
        'uploaded':     uploaded,
        'verified':     verified,
        'pct':          pct,
    }
    return render(request, 'dokumen/daftar_dokumen.html', context)


@login_required
def upload_dokumen(request, dokumen_id):
    """Upload satu dokumen persyaratan"""
    try:
        pendaftaran = Pendaftaran.objects.get(user=request.user)
    except Pendaftaran.DoesNotExist:
        return redirect('dashboard:index')

    dokumen = get_object_or_404(
        DokumenPendaftar,
        id=dokumen_id,
        pendaftaran=pendaftaran
    )

    # Jangan izinkan upload ulang jika sudah terverifikasi
    if dokumen.status_verifikasi == 'terverifikasi':
        messages.info(request, 'Dokumen ini sudah terverifikasi, tidak bisa diubah.')
        return redirect('dokumen:daftar')

    if request.method == 'POST':
        form = UploadDokumenForm(request.POST, request.FILES, instance=dokumen)
        if form.is_valid():
            dok = form.save(commit=False)
            dok.status_verifikasi = 'menunggu'
            dok.tgl_verifikasi    = None
            dok.diverifikasi_oleh = None
            if request.FILES.get('file'):
                dok.nama_file = request.FILES['file'].name
            dok.save()
            messages.success(request, f'Dokumen "{dokumen.nama_dokumen}" berhasil diunggah.')
            return redirect('dokumen:daftar')
    else:
        form = UploadDokumenForm(instance=dokumen)

    return render(request, 'dokumen/upload_dokumen.html', {
        'form':        form,
        'dokumen':     dokumen,
        'pendaftaran': pendaftaran,
    })


@login_required
def hapus_dokumen(request, dokumen_id):
    """Hapus file dokumen (reset ke belum upload)"""
    try:
        pendaftaran = Pendaftaran.objects.get(user=request.user)
    except Pendaftaran.DoesNotExist:
        return redirect('dashboard:index')

    dokumen = get_object_or_404(
        DokumenPendaftar,
        id=dokumen_id,
        pendaftaran=pendaftaran
    )

    if dokumen.status_verifikasi == 'terverifikasi':
        messages.error(request, 'Dokumen sudah terverifikasi, tidak bisa dihapus.')
        return redirect('dokumen:daftar')

    if request.method == 'POST':
        if dokumen.file:
            dokumen.file.delete(save=False)
        dokumen.file              = None
        dokumen.link_drive        = ''
        dokumen.nama_file         = ''
        dokumen.status_verifikasi = 'menunggu'
        dokumen.save()
        messages.success(request, f'Dokumen "{dokumen.nama_dokumen}" berhasil dihapus.')

    return redirect('dokumen:daftar')