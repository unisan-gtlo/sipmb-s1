"""
Helper functions umum untuk app accounts dan terkait identitas user.

Sesuai single-source-of-truth principle: fungsi normalisasi
identitas (nama, email, dll) didefinisikan di sini agar konsisten
di seluruh entry point (form pendaftaran, form edit operator,
sync nama_lengkap di profil, dll).
"""


def normalisasi_nama(nama):
    """
    Normalisasi nama untuk konsistensi data.
    
    Aturan:
    - Convert ke UPPERCASE penuh (sesuai standar ijazah/KTP Indonesia)
    - Strip leading/trailing whitespace
    - TIDAK men-trim spasi internal atau menghapus karakter khusus
      (data masuk apa adanya, hanya format huruf yang konsisten)
    
    Args:
        nama: String nama atau None/empty string
    
    Returns:
        String nama yang sudah ter-normalize, atau input as-is jika kosong/None
    
    Example:
        >>> normalisasi_nama("daffa 'imaduddin")
        "DAFFA 'IMADUDDIN"
        >>> normalisasi_nama("Risal R. Mbuinga ")
        "RISAL R. MBUINGA"
        >>> normalisasi_nama("")
        ""
        >>> normalisasi_nama(None)
        None
    """
    if not nama:
        return nama
    return nama.strip().upper()