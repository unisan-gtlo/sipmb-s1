# pembayaran/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadBuktiForm
from .models import RekeningTujuan, Tagihan



@login_required
def daftar_tagihan(request):
    """List semua tagihan milik maba yang login."""
    tagihan_list = (
        Tagihan.objects
        .filter(pendaftaran__user=request.user)
        .select_related('pendaftaran', 'pendaftaran__gelombang', 'pendaftaran__jalur')
        .order_by('-created_at')
    )
    return render(request, 'pembayaran/daftar.html', {
        'tagihan_list': tagihan_list,
    })
   
@login_required
def detail_tagihan(request, kode_bayar):
    """Detail tagihan + form upload bukti transfer."""
    tagihan = get_object_or_404(
        Tagihan.objects.select_related(
            'pendaftaran',
            'pendaftaran__gelombang',
            'pendaftaran__jalur',
        ),
        kode_bayar=kode_bayar,
        pendaftaran__user=request.user,  # scoping: hanya milik user sendiri
    )

    rekening_aktif = RekeningTujuan.objects.filter(aktif=True)
    konfirmasi_history = tagihan.konfirmasi.all().order_by('-created_at')
    has_pending = konfirmasi_history.filter(status='menunggu').exists()

    bisa_upload = (
        tagihan.status == 'belum_bayar'
        and not has_pending
        and rekening_aktif.exists()
    )

    form = None
    if bisa_upload:
        if request.method == 'POST':
            form = UploadBuktiForm(request.POST, request.FILES)
            if form.is_valid():
                konfirmasi = form.save(commit=False)
                konfirmasi.tagihan = tagihan
                konfirmasi.status = 'menunggu'
                konfirmasi.save()

                # Tagihan pindah ke status menunggu_konfirmasi
                tagihan.status = 'menunggu_konfirmasi'
                tagihan.save(update_fields=['status', 'updated_at'])

                messages.success(
                    request,
                    "Bukti transfer berhasil diupload. "
                    "Admin akan memverifikasi dalam 1×24 jam kerja."
                )
                return redirect('pembayaran:detail', kode_bayar=tagihan.kode_bayar)
        else:
            form = UploadBuktiForm(initial={'jumlah_bayar': tagihan.jumlah})

    return render(request, 'pembayaran/detail.html', {
        'tagihan': tagihan,
        'rekening_aktif': rekening_aktif,
        'konfirmasi_history': konfirmasi_history,
        'bisa_upload': bisa_upload,
        'has_pending': has_pending,
        'form': form,
    })