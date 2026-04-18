"""
Custom file validators untuk upload aman.
"""
import os
from django.core.exceptions import ValidationError

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


# Limit ukuran default: 5 MB
DEFAULT_MAX_SIZE_MB = 1

# MIME type yang diperbolehkan per kategori
ALLOWED_MIMES = {
    'document': [
        'application/pdf',
    ],
    'image': [
        'image/jpeg',
        'image/png',
        'image/webp',
    ],
    'document_image': [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ],
}


def validate_file_size(file, max_mb=DEFAULT_MAX_SIZE_MB):
    """Validasi ukuran file dalam MB."""
    max_bytes = max_mb * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            f'Ukuran file terlalu besar ({file.size / 1024 / 1024:.1f} MB). '
            f'Maksimal {max_mb} MB.'
        )


def validate_file_type(file, category='document_image'):
    """
    Validasi MIME type file dengan membaca konten (bukan extension).
    Lebih aman dari manipulation.
    """
    allowed = ALLOWED_MIMES.get(category, ALLOWED_MIMES['document_image'])
    
    if MAGIC_AVAILABLE:
        # Baca 2048 byte pertama untuk detect MIME
        file.seek(0)
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        
        if mime not in allowed:
            raise ValidationError(
                f'Tipe file tidak diizinkan: {mime}. '
                f'Diizinkan: {", ".join(allowed)}'
            )
    else:
        # Fallback: cek extension saja (kurang aman)
        ext = os.path.splitext(file.name)[1].lower()
        ext_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
        }
        mime = ext_map.get(ext, '')
        if mime not in allowed:
            raise ValidationError(
                f'Ekstensi file tidak diizinkan: {ext}.'
            )


def validate_image(file, max_mb=1):
    """Validasi sebagai image (JPG, PNG, WebP)."""
    validate_file_size(file, max_mb)
    validate_file_type(file, 'image')


def validate_document(file, max_mb=1):
    """Validasi sebagai dokumen (PDF only)."""
    validate_file_size(file, max_mb)
    validate_file_type(file, 'document')


def validate_document_or_image(file, max_mb=1):
    """Validasi sebagai PDF atau gambar (fleksibel untuk upload dokumen pendaftar)."""
    validate_file_size(file, max_mb)
    validate_file_type(file, 'document_image')


def sanitize_filename(filename):
    """Bersihkan nama file dari karakter berbahaya."""
    # Hanya boleh huruf, angka, dash, underscore, dot
    import re
    # Ambil extension
    base, ext = os.path.splitext(filename)
    # Clean base name
    base = re.sub(r'[^\w\-]', '_', base)[:50]
    return f'{base}{ext.lower()}'