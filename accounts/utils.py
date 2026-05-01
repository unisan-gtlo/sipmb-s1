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

def generate_password(panjang=10):
    """
    Generate password random aman untuk pendaftar yang dibuat operator.

    Karakteristik:
    - Menggunakan modul secrets (cryptographically secure, BUKAN random.choice)
    - Hanya pakai huruf besar, huruf kecil, dan angka — tidak pakai simbol
      agar mudah dibacakan via telepon atau ditulis di kertas
    - Hindari karakter ambigu: 0/O, 1/l/I, agar tidak salah ketik

    Args:
        panjang: Panjang password (default 10)

    Returns:
        String password random

    Example:
        >>> generate_password()
        'k7nQpXr3fH'
        >>> generate_password(8)
        'a2BcD9eF'
    """
    import secrets
    import string

    # Karakter aman: alfanumerik tanpa karakter ambigu
    karakter = (
        string.ascii_uppercase.replace('O', '').replace('I', '') +
        string.ascii_lowercase.replace('l', '').replace('o', '') +
        string.digits.replace('0', '').replace('1', '')
    )
    return ''.join(secrets.choice(karakter) for _ in range(panjang))