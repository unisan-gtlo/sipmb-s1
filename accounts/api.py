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