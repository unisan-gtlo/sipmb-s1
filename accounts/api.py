import json
from django.http import JsonResponse
from utils.simda_reader import (
    get_kabupaten_kota, get_kecamatan, get_sekolah
)


def api_kabupaten_kota(request):
    """API: Ambil kab/kota berdasarkan provinsi_id"""
    provinsi_id = request.GET.get('provinsi_id')
    if not provinsi_id:
        return JsonResponse({'data': []})
    data = get_kabupaten_kota(provinsi_id=provinsi_id)
    return JsonResponse({'data': data})


def api_kecamatan(request):
    """API: Ambil kecamatan berdasarkan kabupaten_kota_id"""
    kabupaten_kota_id = request.GET.get('kabupaten_kota_id')
    if not kabupaten_kota_id:
        return JsonResponse({'data': []})
    data = get_kecamatan(kabupaten_kota_id=kabupaten_kota_id)
    return JsonResponse({'data': data})


def api_sekolah(request):
    """API: Autocomplete sekolah"""
    query           = request.GET.get('q', '')
    provinsi_id     = request.GET.get('provinsi_id')
    kabupaten_kota_id = request.GET.get('kabupaten_kota_id')
    if len(query) < 3:
        return JsonResponse({'data': []})
    data = get_sekolah(
        query=query,
        provinsi_id=provinsi_id,
        kabupaten_kota_id=kabupaten_kota_id
    )
    return JsonResponse({'data': data})

# ============================================================
# === API ENDPOINTS UNTUK FILTER DINAMIS DI FORM REGISTRASI
# ============================================================

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from master.models import GelombangPenerimaan, ProdiPMB


@require_GET
def api_gelombang_by_jalur(request):
    """
    Return list gelombang berdasarkan jalur yang dipilih.
    Dipakai di form registrasi untuk filter gelombang.
    Endpoint: /accounts/api/gelombang-by-jalur/?jalur_id=X
    """
    jalur_id = request.GET.get('jalur_id')
    
    if not jalur_id:
        return JsonResponse({'gelombangs': []})
    
    gelombangs = GelombangPenerimaan.objects.filter(
        jalur_id=jalur_id,
        status='buka'
    ).values('id', 'nama_gelombang', 'tahun_akademik')
    
    data = [
        {
            'id': g['id'],
            'label': f"{g['nama_gelombang']} ({g['tahun_akademik']})"
        }
        for g in gelombangs
    ]
    
    return JsonResponse({'gelombangs': data})


@require_GET
def api_prodi_by_gelombang(request):
    """
    Return list prodi (aktif) berdasarkan gelombang yang dipilih.
    Dipakai di form registrasi untuk filter prodi pilihan 1 & 2.
    Endpoint: /accounts/api/prodi-by-gelombang/?gelombang_id=X
    """
    gelombang_id = request.GET.get('gelombang_id')
    
    if not gelombang_id:
        return JsonResponse({'prodis': []})
    
    prodis = ProdiPMB.objects.filter(
        gelombang_id=gelombang_id,
        status='aktif'
    ).values('id', 'nama_prodi', 'nama_fakultas', 'kuota')
    
    data = [
        {
            'id': p['id'],
            'label': p['nama_prodi'],
            'fakultas': p.get('nama_fakultas', '') or '',
            'kuota': p.get('kuota', 0) or 0
        }
        for p in prodis
    ]
    
    return JsonResponse({'prodis': data})