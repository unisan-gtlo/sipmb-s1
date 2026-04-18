"""
Context processors untuk inject data global ke semua template.
"""
from .models import PengaturanSistem


def pengaturan_global(request):
    """
    Inject pengaturan sistem ke semua template.
    
    Dipakai di footer, header, dll agar admin bisa update data
    lewat admin panel tanpa ubah template.
    
    Method get() pada model auto-create record dengan pk=1 kalau
    belum ada, jadi aman dari error.
    """
    try:
        pengaturan = PengaturanSistem.get()
    except Exception:
        pengaturan = None
    return {
        'pengaturan': pengaturan,
    }