from django.db import connections


def _fetch(sql, params=None):
    """Helper eksekusi query ke SIMDA (schema master)"""
    with connections['simda'].cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_provinsi():
    return _fetch("""
        SELECT id, nama_provinsi as nama
        FROM master.provinsi
        WHERE status = true
        ORDER BY nama_provinsi
    """)


def get_kabupaten_kota(provinsi_id=None):
    sql_select = """
        SELECT id,
               CONCAT(jenis, ' ', nama) as nama
        FROM master.kabupaten_kota
        WHERE status = true
    """
    if provinsi_id:
        return _fetch(sql_select + " AND provinsi_id = %s ORDER BY nama", [provinsi_id])
    return _fetch(sql_select + " ORDER BY nama")


def get_kecamatan(kabupaten_kota_id=None):
    if kabupaten_kota_id:
        return _fetch("""
            SELECT id, nama
            FROM master.kecamatan
            WHERE kabupaten_kota_id = %s AND status = true
            ORDER BY nama
        """, [kabupaten_kota_id])
    return []


def get_sekolah(query=None, provinsi_id=None, kabupaten_kota_id=None):
    """Autocomplete sekolah"""
    sql = """
        SELECT id, npsn, nama_sekolah, alamat,
               kabupaten_kota_id, provinsi_id
        FROM master.sekolah
        WHERE status = true
    """
    params = []
    if query:
        sql += " AND LOWER(nama_sekolah) LIKE LOWER(%s)"
        params.append(f'%{query}%')
    if kabupaten_kota_id:
        sql += " AND kabupaten_kota_id = %s"
        params.append(kabupaten_kota_id)
    elif provinsi_id:
        sql += " AND provinsi_id = %s"
        params.append(provinsi_id)
    sql += " ORDER BY nama_sekolah LIMIT 20"
    return _fetch(sql, params)


def get_jurusan_sekolah():
    """Jurusan SMA/SMK dari master"""
    # Jurusan SMA umum + jurusan SMK dari master
    jurusan_sma = [
        {'id': 'IPA',    'nama': 'IPA (Ilmu Pengetahuan Alam)'},
        {'id': 'IPS',    'nama': 'IPS (Ilmu Pengetahuan Sosial)'},
        {'id': 'BAHASA', 'nama': 'Bahasa & Sastra'},
        {'id': 'AGAMA',  'nama': 'Ilmu Agama'},
    ]
    jurusan_smk = _fetch("""
        SELECT id::text as id,
               CONCAT(nama_jurusan, ' (', bidang_keahlian, ')') as nama
        FROM master.jurusan_smk
        WHERE status = true
        ORDER BY bidang_keahlian, nama_jurusan
        LIMIT 100
    """)
    return jurusan_sma + jurusan_smk


def get_agama():
    return _fetch("""
        SELECT id, kode, nama
        FROM master.agama
        WHERE status = true
        ORDER BY urutan
    """)


def get_fakultas():
    return _fetch("""
        SELECT kode_fakultas, nama_fakultas, nama_singkat, akreditasi
        FROM master.fakultas
        WHERE status = 'aktif'
        ORDER BY urutan
    """)


def get_program_studi(kode_fakultas=None, jenjang=None):
    sql = """
        SELECT ps.kode_prodi, ps.nama_prodi, ps.jenjang,
               ps.akreditasi, ps.kode_fakultas,
               f.nama_fakultas
        FROM master.program_studi ps
        JOIN master.fakultas f ON ps.kode_fakultas = f.kode_fakultas
        WHERE ps.status = 'aktif'
    """
    params = []
    if kode_fakultas:
        sql += " AND ps.kode_fakultas = %s"
        params.append(kode_fakultas)
    if jenjang:
        sql += " AND ps.jenjang = %s"
        params.append(jenjang)
    sql += " ORDER BY f.urutan, ps.urutan"
    return _fetch(sql, params)


def get_tahun_akademik_aktif():
    rows = _fetch("""
        SELECT id, tahun_akademik, semester_aktif, label_lengkap
        FROM master.tahun_akademik
        WHERE is_aktif = true
        LIMIT 1
    """)
    return rows[0] if rows else None


def get_institusi():
    rows = _fetch("""
        SELECT * FROM master.institusi LIMIT 1
    """)
    return rows[0] if rows else None 
