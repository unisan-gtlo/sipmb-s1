from django.db import connections


def _fetch(sql, params=None):
    """Helper eksekusi query ke SIMDA (schema master)"""
    with connections['simda'].cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


# ============================================================
# WILAYAH
# ============================================================

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


# ============================================================
# SEKOLAH & JURUSAN
# ============================================================

def get_sekolah(query=None, provinsi_id=None, kabupaten_kota_id=None):
    """Autocomplete sekolah, return juga kode jenjang (SMA/SMK/MA/MAK)"""
    sql = """
        SELECT s.id, s.npsn, s.nama_sekolah, s.alamat,
               s.kabupaten_kota_id, s.provinsi_id,
               s.jenis_sekolah_id, js.kode AS jenjang_kode
        FROM master.sekolah s
        LEFT JOIN master.jenis_sekolah js ON s.jenis_sekolah_id = js.id
        WHERE s.status = true
    """
    params = []
    if query:
        sql += " AND LOWER(s.nama_sekolah) LIKE LOWER(%s)"
        params.append(f'%{query}%')
    if kabupaten_kota_id:
        sql += " AND s.kabupaten_kota_id = %s"
        params.append(kabupaten_kota_id)
    elif provinsi_id:
        sql += " AND s.provinsi_id = %s"
        params.append(provinsi_id)
    sql += " ORDER BY s.nama_sekolah LIMIT 20"
    return _fetch(sql, params)


def get_jurusan_sekolah():
    """Jurusan SMA/SMK dari master"""
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


# ============================================================
# AGAMA
# ============================================================

def get_agama():
    return _fetch("""
        SELECT id, kode, nama
        FROM master.agama
        WHERE status = true
        ORDER BY urutan
    """)


# ============================================================
# FAKULTAS & PROGRAM STUDI (UNISAN)
# ============================================================

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


# ============================================================
# TAHUN AKADEMIK & INSTITUSI
# ============================================================

def get_tahun_akademik_aktif():
    rows = _fetch("""
        SELECT id, tahun_akademik, semester_aktif, label_lengkap
        FROM master.tahun_akademik
        WHERE is_aktif = true
        LIMIT 1
    """)
    return rows[0] if rows else None


def get_institusi():
    """Ambil data institusi UNISAN dari SIMDA"""
    hasil = _fetch("""
        SELECT id, kode, nama_resmi, nama_singkat, npsn,
               alamat, kabupaten, provinsi, kode_pos,
               telepon, email, website, akreditasi, logo
        FROM master.institusi
        LIMIT 1
    """)
    return hasil[0] if hasil else {}


# ============================================================
# PERGURUAN TINGGI (untuk maba pindahan)
# ============================================================

def get_perguruan_tinggi(search=None, limit=50):
    """
    Ambil daftar PT dari master.perguruan_tinggi di SIMDA.
    - search: keyword pencarian nama PT untuk autocomplete
    - limit: batasi jumlah hasil (default 50)
    Return: list of dict {id, kode_pt, nama, nama_singkat, jenis}
    """
    sql = """
        SELECT id,
               COALESCE(kode_pt, '')      as kode_pt,
               nama_pt                     as nama,
               COALESCE(nama_singkat, '') as nama_singkat,
               COALESCE(jenis_pt, '')     as jenis
        FROM master.perguruan_tinggi
        WHERE status = true
    """
    params = []
    if search:
        sql += " AND (LOWER(nama_pt) LIKE LOWER(%s) OR LOWER(nama_singkat) LIKE LOWER(%s) OR LOWER(kode_pt) LIKE LOWER(%s))"
        like = f'%{search}%'
        params = [like, like, like]
    sql += " ORDER BY nama_pt LIMIT %s"
    params.append(limit)
    return _fetch(sql, params)


def get_perguruan_tinggi_by_id(pt_id):
    """Ambil 1 PT berdasarkan ID — return dict atau None"""
    if not pt_id:
        return None
    rows = _fetch("""
        SELECT id,
               COALESCE(kode_pt, '')      as kode_pt,
               nama_pt                     as nama,
               COALESCE(nama_singkat, '') as nama_singkat,
               COALESCE(jenis_pt, '')     as jenis
        FROM master.perguruan_tinggi
        WHERE id = %s AND status = true
        LIMIT 1
    """, [pt_id])
    return rows[0] if rows else None


def get_prodi_pt(perguruan_tinggi_id=None, search=None, limit=100):
    """
    Ambil daftar prodi dari master.prodi_pt di SIMDA.
    - perguruan_tinggi_id: filter prodi milik PT tertentu
    - search: keyword nama prodi
    Return: list of dict {id, kode, nama, jenjang, akreditasi}
    """
    sql = """
        SELECT id,
               COALESCE(kode_prodi_dikti, '') as kode,
               nama_prodi                      as nama,
               COALESCE(jenjang, '')          as jenjang,
               COALESCE(akreditasi, '')       as akreditasi
        FROM master.prodi_pt
        WHERE status = true
    """
    params = []
    if perguruan_tinggi_id:
        sql += " AND perguruan_tinggi_id = %s"
        params.append(perguruan_tinggi_id)
    if search:
        sql += " AND LOWER(nama_prodi) LIKE LOWER(%s)"
        params.append(f'%{search}%')
    sql += " ORDER BY jenjang, nama_prodi LIMIT %s"
    params.append(limit)
    return _fetch(sql, params)