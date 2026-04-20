# pembayaran/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadBuktiForm
from .models import RekeningTujuan, Tagihan
from django.http import Http404, HttpResponse
from .pdf import generate_kwitansi_pdf
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

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

@login_required
def kwitansi(request, kode_bayar):
    """Cetak kwitansi PDF — hanya untuk tagihan lunas milik maba sendiri."""
    tagihan = get_object_or_404(
        Tagihan.objects.select_related('pendaftaran', 'pendaftaran__user'),
        kode_bayar=kode_bayar,
        pendaftaran__user=request.user,
    )
    if tagihan.status != 'lunas':
        raise Http404("Kwitansi hanya tersedia untuk tagihan yang sudah lunas.")

    konfirmasi = tagihan.konfirmasi.filter(status='dikonfirmasi').order_by('-tgl_konfirmasi').first()
    if not konfirmasi:
        raise Http404("Data konfirmasi tidak ditemukan.")

    buffer = generate_kwitansi_pdf(konfirmasi)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Kwitansi-{tagihan.kode_bayar}.pdf"'
    return response

@login_required
def duitku_pilih_metode(request, kode_bayar):
    """Halaman pilih metode pembayaran online (Duitku)."""
    tagihan = get_object_or_404(
        Tagihan.objects.select_related('pendaftaran', 'pendaftaran__user'),
        kode_bayar=kode_bayar,
        pendaftaran__user=request.user,
    )

    if tagihan.status == 'lunas':
        messages.info(request, "Tagihan ini sudah lunas.")
        return redirect('pembayaran:detail', kode_bayar=kode_bayar)

    # Daftar metode yang ditampilkan ke maba
    METODE_LIST = [
        # kode, label, kategori, icon_text
        ('BC', 'BCA Virtual Account', 'Virtual Account', 'BCA'),
        ('M2', 'Mandiri Virtual Account', 'Virtual Account', 'MDR'),
        ('I1', 'BNI Virtual Account', 'Virtual Account', 'BNI'),
        ('B1', 'CIMB Niaga Virtual Account', 'Virtual Account', 'CIMB'),
        ('BT', 'Permata Virtual Account', 'Virtual Account', 'PERMATA'),
        ('A1', 'ATM Bersama', 'Virtual Account', 'ATM'),
        ('SP', 'ShopeePay', 'E-Wallet', 'SP'),
        ('OV', 'OVO', 'E-Wallet', 'OVO'),
        ('DA', 'DANA', 'E-Wallet', 'DANA'),
        ('LF', 'LinkAja', 'E-Wallet', 'LINK'),
        ('NQ', 'QRIS', 'QRIS', 'QR'),
        ('SL', 'Indomaret', 'Gerai Retail', 'INDO'),
        ('FT', 'Alfamart', 'Gerai Retail', 'ALFA'),
        ('VC', 'Credit Card', 'Kartu Kredit', 'CC'),
    ]

    return render(request, 'pembayaran/duitku_pilih.html', {
        'tagihan': tagihan,
        'metode_list': METODE_LIST,
    })


@login_required
def duitku_create(request, kode_bayar):
    """Handle POST dari halaman pilih metode → request ke Duitku → redirect ke paymentUrl."""
    if request.method != 'POST':
        return redirect('pembayaran:duitku_pilih', kode_bayar=kode_bayar)

    tagihan = get_object_or_404(
        Tagihan.objects.select_related('pendaftaran', 'pendaftaran__user'),
        kode_bayar=kode_bayar,
        pendaftaran__user=request.user,
    )

    if tagihan.status == 'lunas':
        messages.info(request, "Tagihan ini sudah lunas.")
        return redirect('pembayaran:detail', kode_bayar=kode_bayar)

    payment_method = (request.POST.get('payment_method') or '').strip()
    if not payment_method:
        messages.error(request, "Pilih metode pembayaran terlebih dahulu.")
        return redirect('pembayaran:duitku_pilih', kode_bayar=kode_bayar)

    # Build absolute URL return & callback (harus HTTPS kalau production)
    return_url = request.build_absolute_uri(
        reverse('pembayaran:duitku_return')
    )
    callback_url = request.build_absolute_uri(
        reverse('pembayaran:duitku_callback')
    )

    # Request ke Duitku
    from .duitku_client import request_transaction
    result = request_transaction(
        tagihan,
        return_url=return_url,
        callback_url=callback_url,
        payment_method=payment_method,
    )

    if not result.get('success'):
        # Debug — tampilkan raw error Duitku
        raw = result.get('raw', {})
        error_msg = result.get('error') or raw.get('Message') or 'Unknown error'
        messages.error(
            request,
            f"Gagal: {error_msg} | Raw: {raw} | Method: {payment_method}"
        )
        return redirect('pembayaran:duitku_pilih', kode_bayar=kode_bayar)

    # Simpan transaksi untuk tracking
    from .models import TransaksiDuitku
    TransaksiDuitku.objects.create(
        tagihan=tagihan,
        merchant_order_id=result['merchant_order_id'],
        reference=result.get('reference', ''),
        payment_method=payment_method,
        payment_url=result.get('payment_url', ''),
        va_number=result.get('va_number', ''),
        amount=tagihan.jumlah,
        status='pending',
    )

    # Update tagihan ke status menunggu_konfirmasi
    tagihan.status = 'menunggu_konfirmasi'
    tagihan.save(update_fields=['status', 'updated_at'])

    return redirect(result['payment_url'])


@login_required
def duitku_return(request):
    """Halaman landing setelah user selesai bayar di Duitku."""
    from django.utils import timezone
    from .models import TransaksiDuitku, KonfirmasiPembayaran
    from .duitku_client import check_transaction_status

    merchant_order_id = request.GET.get('merchantOrderId', '').strip()
    reference = request.GET.get('reference', '').strip()

    transaksi = None
    tagihan = None

    if merchant_order_id:
        transaksi = TransaksiDuitku.objects.filter(
            merchant_order_id=merchant_order_id,
            tagihan__pendaftaran__user=request.user,
        ).select_related('tagihan').first()

        # Polling: kalau masih pending, cek langsung ke Duitku
        if transaksi and transaksi.status == 'pending':
            try:
                result = check_transaction_status(merchant_order_id)
                if result.get('success') and result.get('status') == 'paid':
                    # Update lokal seperti callback (defensive — in case callback gagal)
                    transaksi.status = 'paid'
                    transaksi.tgl_paid = timezone.now()
                    transaksi.save()

                    tag = transaksi.tagihan
                    if tag.status != 'lunas':
                        tag.status = 'lunas'
                        tag.save(update_fields=['status', 'updated_at'])

                        KonfirmasiPembayaran.objects.create(
                            tagihan=tag,
                            metode_bayar='qris' if transaksi.payment_method in ('NQ', 'SP') else 'transfer_bank',
                            jumlah_bayar=transaksi.amount,
                            tgl_bayar=timezone.now().date(),
                            no_transaksi=transaksi.reference,
                            status='dikonfirmasi',
                            tgl_konfirmasi=timezone.now(),
                            catatan_admin=f'Auto-konfirmasi via Duitku polling. Order: {merchant_order_id}',
                            atas_nama_pengirim=tag.pendaftaran.user.get_full_name() or '(via Duitku)',
                        )
            except Exception:
                pass  # Kalau API error, tampilkan data dari DB

        if transaksi:
            tagihan = transaksi.tagihan

    return render(request, 'pembayaran/duitku_return.html', {
        'transaksi': transaksi,
        'tagihan': tagihan,
        'merchant_order_id': merchant_order_id,
        'reference': reference,
    })

@csrf_exempt
def duitku_callback(request):
    """
    Webhook POST dari Duitku saat status pembayaran berubah.
    
    Duitku POST x-www-form-urlencoded dengan fields:
    - merchantCode
    - amount
    - merchantOrderId
    - productDetail
    - additionalParam
    - paymentCode
    - resultCode ('00' = success, '01' = failed)
    - merchantUserId
    - reference
    - signature
    
    Response: HTTP 200 + body "OK" kalau diproses
              HTTP 400 kalau signature invalid
    """
    import logging
    from django.utils import timezone
    from .models import TransaksiDuitku, KonfirmasiPembayaran
    from .duitku_client import verify_callback_signature
    
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
    
    merchant_code = request.POST.get('merchantCode', '').strip()
    amount = request.POST.get('amount', '').strip()
    merchant_order_id = request.POST.get('merchantOrderId', '').strip()
    result_code = request.POST.get('resultCode', '').strip()
    signature = request.POST.get('signature', '').strip()
    reference = request.POST.get('reference', '').strip()
    
    logger.info(
        f"Duitku callback: orderId={merchant_order_id} resultCode={result_code} "
        f"amount={amount} ref={reference}"
    )
    
    # Minimum required fields
    if not all([merchant_code, amount, merchant_order_id, signature]):
        logger.warning(f"Duitku callback missing required fields: {dict(request.POST)}")
        return HttpResponse("Missing required fields", status=400)
    
    # Verify signature — ini security check paling penting
    if not verify_callback_signature(merchant_code, amount, merchant_order_id, signature):
        logger.error(f"Duitku callback INVALID SIGNATURE for orderId={merchant_order_id}")
        return HttpResponse("Invalid signature", status=400)
    
    # Find transaksi
    try:
        transaksi = TransaksiDuitku.objects.select_related('tagihan').get(
            merchant_order_id=merchant_order_id
        )
    except TransaksiDuitku.DoesNotExist:
        logger.error(f"Duitku callback: transaksi tidak ditemukan for {merchant_order_id}")
        # Return 200 supaya Duitku tidak retry terus
        return HttpResponse("Transaction not found", status=200)
    
    # Update transaksi
    transaksi.callback_payload = dict(request.POST)
    transaksi.reference = reference or transaksi.reference
    transaksi.signature = signature
    
    if result_code == '00':
        # PAYMENT SUCCESS
        transaksi.status = 'paid'
        transaksi.tgl_paid = timezone.now()
        transaksi.save()
        
        tagihan = transaksi.tagihan
        
        # Guard: kalau tagihan sudah lunas (misal dari konfirmasi manual), skip
        if tagihan.status != 'lunas':
            tagihan.status = 'lunas'
            tagihan.save(update_fields=['status', 'updated_at'])
            
            # Buat entry KonfirmasiPembayaran auto untuk unified log
            KonfirmasiPembayaran.objects.create(
                tagihan=tagihan,
                metode_bayar='qris' if transaksi.payment_method in ('NQ', 'SP') else 'transfer_bank',
                jumlah_bayar=transaksi.amount,
                tgl_bayar=timezone.now().date(),
                no_transaksi=reference,
                status='dikonfirmasi',
                tgl_konfirmasi=timezone.now(),
                catatan_admin=f'Auto-konfirmasi via Duitku. Order: {merchant_order_id}',
                atas_nama_pengirim=tagihan.pendaftaran.user.get_full_name() or '(via Duitku)',
            )
            
            logger.info(f"Duitku callback SUCCESS: tagihan {tagihan.kode_bayar} marked as LUNAS")
        
    elif result_code == '01':
        # PAYMENT FAILED
        transaksi.status = 'failed'
        transaksi.save()
        logger.info(f"Duitku callback FAILED: {merchant_order_id}")
        
        # Rollback tagihan ke belum_bayar kalau tidak ada transaksi lain aktif
        tagihan = transaksi.tagihan
        has_other_active = tagihan.transaksi_duitku.exclude(
            pk=transaksi.pk
        ).filter(status__in=('pending', 'paid')).exists()
        if not has_other_active and tagihan.status == 'menunggu_konfirmasi':
            tagihan.status = 'belum_bayar'
            tagihan.save(update_fields=['status', 'updated_at'])
    else:
        # Status lain — log saja
        transaksi.save()
        logger.info(f"Duitku callback unknown resultCode={result_code}: {merchant_order_id}")
    
    return HttpResponse("OK", status=200)