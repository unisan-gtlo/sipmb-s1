"""
Service helper untuk setup bulk prodi per gelombang.
"""

from django.db import transaction
from utils.simda_reader import get_program_studi
from master.models import ProdiPMB, GelombangPenerimaan


def get_matrix_prodi(gelombang):
    """
    Build matrix data: gabung semua prodi dari SIMDA + status existing di ProdiPMB
    untuk gelombang tertentu.

    Returns: list of dict, satu dict per prodi dengan status checked + nilai existing.
    """
    # Ambil semua prodi aktif dari SIMDA master
    prodi_master = get_program_studi()

    # Ambil ProdiPMB yang sudah ada untuk gelombang ini
    existing = {
        p.kode_prodi: p
        for p in ProdiPMB.objects.filter(gelombang=gelombang)
    }

    matrix = []
    for prodi in prodi_master:
        kode = prodi['kode_prodi']
        existing_obj = existing.get(kode)

        matrix.append({
            'kode_prodi':    kode,
            'nama_prodi':    prodi['nama_prodi'],
            'jenjang':       prodi['jenjang'],
            'akreditasi':    prodi['akreditasi'],
            'kode_fakultas': prodi['kode_fakultas'],
            'nama_fakultas': prodi['nama_fakultas'],
            'is_checked':    existing_obj is not None,
            'kuota':         existing_obj.kuota if existing_obj else 30,
            'daya_tampung':  existing_obj.daya_tampung if existing_obj else 30,
            'biaya_kuliah':  int(existing_obj.biaya_kuliah) if existing_obj else 0,
            'biaya_spp':     int(existing_obj.biaya_spp) if existing_obj else 0,
            'is_aktif':      existing_obj.status == 'aktif' if existing_obj else True,
        })
    return matrix


@transaction.atomic
def save_matrix_prodi(gelombang, rows_data):
    """
    Save bulk matrix:
    - Create/update ProdiPMB untuk row yang is_checked
    - Delete ProdiPMB untuk row yang TIDAK is_checked tapi sebelumnya ada

    rows_data: list of dict dari form POST, struktur per item:
        {
            'kode_prodi': str,
            'nama_prodi': str,
            'kode_fakultas': str,
            'nama_fakultas': str,
            'is_checked': bool,
            'kuota': int,
            'daya_tampung': int,
            'biaya_kuliah': int,
            'biaya_spp': int,
        }

    Returns: dict dengan jumlah created, updated, deleted.
    """
    counts = {'created': 0, 'updated': 0, 'deleted': 0}

    # Set existing kode_prodi yang sudah ada untuk gelombang ini
    existing_kode = set(
        ProdiPMB.objects.filter(gelombang=gelombang).values_list('kode_prodi', flat=True)
    )

    submitted_kode = set()

    for row in rows_data:
        kode = row['kode_prodi']
        submitted_kode.add(kode)

        if not row['is_checked']:
            continue

        defaults = {
            'nama_prodi':    row['nama_prodi'],
            'kode_fakultas': row['kode_fakultas'],
            'nama_fakultas': row['nama_fakultas'],
            'kuota':         max(0, int(row.get('kuota') or 0)),
            'daya_tampung':  max(0, int(row.get('daya_tampung') or 0)),
            'biaya_kuliah':  max(0, int(row.get('biaya_kuliah') or 0)),
            'biaya_spp':     max(0, int(row.get('biaya_spp') or 0)),
            'status':        'aktif',
        }

        obj, created = ProdiPMB.objects.update_or_create(
            kode_prodi=kode,
            gelombang=gelombang,
            defaults=defaults,
        )
        if created:
            counts['created'] += 1
        else:
            counts['updated'] += 1

    # Hapus row yang ada di DB tapi tidak di-checked
    to_delete = existing_kode - submitted_kode
    # Plus row yang ada di submitted tapi unchecked
    unchecked = {row['kode_prodi'] for row in rows_data if not row['is_checked']}
    to_delete = to_delete | (unchecked & existing_kode)

    if to_delete:
        deleted_count = ProdiPMB.objects.filter(
            gelombang=gelombang,
            kode_prodi__in=to_delete,
        ).count()
        ProdiPMB.objects.filter(
            gelombang=gelombang,
            kode_prodi__in=to_delete,
        ).delete()
        counts['deleted'] = deleted_count

    return counts


@transaction.atomic
def clone_prodi_gelombang(source_gelombang, target_gelombang):
    """
    Copy semua ProdiPMB dari source ke target gelombang.
    Override yang sudah ada di target.

    Returns: dict dengan count created, updated.
    """
    counts = {'created': 0, 'updated': 0}

    source_prodi = ProdiPMB.objects.filter(gelombang=source_gelombang)

    for sp in source_prodi:
        defaults = {
            'nama_prodi':    sp.nama_prodi,
            'kode_fakultas': sp.kode_fakultas,
            'nama_fakultas': sp.nama_fakultas,
            'kuota':         sp.kuota,
            'daya_tampung':  sp.daya_tampung,
            'biaya_kuliah':  sp.biaya_kuliah,
            'biaya_spp':     sp.biaya_spp,
            'status':        sp.status,
        }
        _, created = ProdiPMB.objects.update_or_create(
            kode_prodi=sp.kode_prodi,
            gelombang=target_gelombang,
            defaults=defaults,
        )
        if created:
            counts['created'] += 1
        else:
            counts['updated'] += 1

    return counts


def get_gelombang_with_count():
    """Ambil semua gelombang + count prodi yang sudah disetup."""
    from django.db.models import Count
    return GelombangPenerimaan.objects.annotate(
        total_prodi=Count('prodi_pmb', filter=None)
    ).select_related('jalur').order_by('-tahun_akademik', '-tgl_buka')