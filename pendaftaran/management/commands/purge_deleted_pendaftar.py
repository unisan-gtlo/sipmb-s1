"""
Management command: Hard delete pendaftar yang sudah di-soft-delete.

Hanya menghapus pendaftar yang:
- is_deleted = True
- deleted_at lebih dari N hari yang lalu (default 30)

Default mode: --dry-run (hanya preview, tidak hapus).
Untuk benar-benar apply, pakai flag --apply.

Cascade delete: Pendaftaran + User + semua data terkait
(ProfilPendaftar, DokumenPendaftar, Tagihan, KonfirmasiPembayaran,
PesertaSeleksi, HasilPenerimaan, KartuPeserta, LogStatusPendaftaran,
LogEditDataPendaftar, dll. — sesuai on_delete=CASCADE di model).

Usage:
    # Preview yang akan di-purge (cooldown default 30 hari)
    python manage.py purge_deleted_pendaftar
    
    # Preview dengan cooldown lebih singkat
    python manage.py purge_deleted_pendaftar --older-than 7
    
    # Apply (eksekusi hard delete) dengan cooldown default
    python manage.py purge_deleted_pendaftar --apply
    
    # Apply dengan cooldown 0 (langsung purge semua yang ditandai hapus)
    python manage.py purge_deleted_pendaftar --apply --older-than 0
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from pendaftaran.models import Pendaftaran


class Command(BaseCommand):
    help = 'Hard delete pendaftar yang sudah di-soft-delete lebih dari N hari (default 30 hari).'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply perubahan (eksekusi hard delete). Tanpa flag ini, hanya dry-run (preview).',
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=30,
            help='Minimum hari sejak deleted_at agar masuk daftar purge (default: 30).',
        )
    
    def handle(self, *args, **options):
        apply_changes = options['apply']
        older_than_days = options['older_than']
        
        cutoff_date = timezone.now() - timedelta(days=older_than_days)
        
        # Build queryset
        qs = Pendaftaran.all_objects.filter(
            is_deleted=True,
            deleted_at__lte=cutoff_date,
        ).select_related('user', 'deleted_by').order_by('deleted_at')
        
        total = qs.count()
        mode_label = 'APPLY (akan HARD DELETE dari DB)' if apply_changes else 'DRY-RUN (hanya preview)'
        
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{"="*70}\n'
            f'Purge Pendaftar Soft-Deleted\n'
            f'{"="*70}'
        ))
        self.stdout.write(f'Mode             : {mode_label}')
        self.stdout.write(f'Cooldown         : {older_than_days} hari (cutoff: {cutoff_date.strftime("%Y-%m-%d %H:%M")})')
        self.stdout.write(f'Total kandidat   : {total}')
        self.stdout.write('')
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                f'Tidak ada pendaftar yang memenuhi kriteria purge.'
            ))
            
            # Info tambahan untuk admin
            soft_deleted_total = Pendaftaran.all_objects.filter(is_deleted=True).count()
            if soft_deleted_total > 0:
                self.stdout.write(self.style.WARNING(
                    f'\nCatatan: ada {soft_deleted_total} pendaftar dalam status terhapus, '
                    f'tapi belum mencapai cooldown {older_than_days} hari.'
                ))
                self.stdout.write(self.style.WARNING(
                    f'Pakai --older-than 0 untuk purge tanpa cooldown.'
                ))
            return
        
        # Tampilkan preview
        self.stdout.write(self.style.MIGRATE_LABEL(
            f'Akan PURGE (HARD DELETE) {total} pendaftar:'
        ))
        self.stdout.write('')
        self.stdout.write(f'{"NO. PENDAFTARAN":<20} {"NAMA":<35} {"DELETED AT":<20} {"BY":<15}')
        self.stdout.write('-' * 90)
        
        for p in qs:
            nama = f'{p.user.first_name} {p.user.last_name}'.strip()
            deleted_at = p.deleted_at.strftime('%Y-%m-%d %H:%M') if p.deleted_at else 'N/A'
            deleted_by = p.deleted_by.username if p.deleted_by else 'N/A'
            self.stdout.write(f'{p.no_pendaftaran:<20} {nama[:34]:<35} {deleted_at:<20} {deleted_by:<15}')
        
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            'Cascade delete akan menghapus:\n'
            '  - User account\n'
            '  - ProfilPendaftar\n'
            '  - DokumenPendaftar (file fisik tetap di disk, perlu cleanup terpisah)\n'
            '  - Tagihan & KonfirmasiPembayaran\n'
            '  - PesertaSeleksi & HasilPenerimaan & KartuPeserta\n'
            '  - LogStatusPendaftaran & LogEditDataPendaftar\n'
        ))
        
        # Apply jika diminta
        if not apply_changes:
            self.stdout.write(self.style.WARNING(
                f'\nDRY-RUN selesai. Untuk benar-benar apply, jalankan ulang dengan flag --apply\n'
                f'  python manage.py purge_deleted_pendaftar --apply --older-than {older_than_days}\n'
            ))
            return
        
        # APPLY mode — wrap dalam atomic
        self.stdout.write(self.style.MIGRATE_HEADING('Memulai HARD DELETE...'))
        
        n_deleted = 0
        with transaction.atomic():
            for p in qs:
                user = p.user  # Save reference sebelum p.delete()
                no_pendaftaran = p.no_pendaftaran
                
                # Delete Pendaftaran (cascade ke profil, dokumen, tagihan, dll)
                p.delete()
                
                # Delete User (kalau Pendaftaran sudah ke-delete, User-nya jadi orphan)
                if user:
                    user.delete()
                
                n_deleted += 1
                self.stdout.write(f'  ✓ {no_pendaftaran} purged')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Selesai. {n_deleted} pendaftar ter-hard-delete dari database.\n'
        ))