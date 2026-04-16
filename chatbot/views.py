import uuid
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .engine import proses_pesan
from .models import SesiChat, RiwayatChat

logger = logging.getLogger(__name__)


@require_http_methods(['POST'])
def kirim_pesan(request):
    """API endpoint untuk kirim pesan ke SINTA"""
    try:
        data       = json.loads(request.body)
        pesan      = data.get('pesan', '').strip()
        session_id = data.get('session_id', '')
        nama_tamu  = data.get('nama_tamu', '')

        if not pesan:
            return JsonResponse({'error': 'Pesan tidak boleh kosong'}, status=400)

        # Generate session ID baru jika belum ada
        if not session_id:
            session_id = str(uuid.uuid4())

        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
             or request.META.get('REMOTE_ADDR', '')

        hasil = proses_pesan(
            session_id=session_id,
            pesan=pesan,
            user=request.user if request.user.is_authenticated else None,
            nama_tamu=nama_tamu,
            ip=ip,
        )
        return JsonResponse(hasil)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format request tidak valid'}, status=400)
    except Exception as e:
        logger.error(f'Error kirim_pesan: {e}')
        return JsonResponse({'error': 'Terjadi kesalahan server'}, status=500)


@require_http_methods(['GET'])
def riwayat_sesi(request, session_id):
    """Ambil riwayat percakapan satu sesi"""
    try:
        sesi   = SesiChat.objects.get(session_id=session_id)
        pesan  = sesi.pesan.all().order_by('tgl_kirim')
        data   = [{
            'pengirim': p.pengirim,
            'pesan':    p.pesan,
            'waktu':    p.tgl_kirim.strftime('%H:%M'),
        } for p in pesan]
        return JsonResponse({'data': data})
    except SesiChat.DoesNotExist:
        return JsonResponse({'data': []})