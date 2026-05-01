"""
Management command: Backfill normalisasi nama (UPPERCASE) ke User existing.

Default mode: --dry-run (hanya preview, tidak simpan).
Untuk benar-benar apply, pakai flag --apply.

Usage:
    # Preview perubahan untuk semua user
    python manage.py normalisasi_nama_existing
    
    # Preview untuk role tertentu
    python manage.py normalisasi_nama_existing --role calon_maba
    
    # Apply perubahan ke DB
    python manage.py normalisasi_nama_existing --apply
    
    # Apply hanya untuk role tertentu
    python manage.py normalisasi_nama_existing --apply --role calon_maba
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from accounts.utils import normalisasi_nama


class Command(BaseCommand):
    help = 'Normalisasi (UPPERCASE) first_name & last_name semua User existing.'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply perubahan ke DB. Tanpa flag ini, hanya dry-run (preview).',
        )
        parser.add_argument(
            '--role',
            type=str,
            default=None,
            help='Filter berdasarkan role (cth: calon_maba, recruiter). Default: semua role.',
        )
    
    def handle(self, *args, **options):
        apply_changes = options['apply']
        role_filter = options['role']
        
        # Build queryset
        qs = User.objects.all()
        if role_filter:
            qs = qs.filter(role=role_filter)
        
        total = qs.count()
        mode_label = 'APPLY (akan menyimpan ke DB)' if apply_changes else 'DRY-RUN (hanya preview)'
        
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{"="*70}\n'
            f'Normalisasi Nama User\n'
            f'{"="*70}'
        ))
        self.stdout.write(f'Mode       : {mode_label}')
        self.stdout.write(f'Filter role: {role_filter if role_filter else "(semua)"}')
        self.stdout.write(f'Total user : {total}')
        self.stdout.write('')
        
        if total == 0:
            self.stdout.write(self.style.WARNING('Tidak ada user yang cocok dengan filter.'))
            return
        
        # Iterate dan kumpulkan perubahan
        changes = []  # list of (user, old_first, old_last, new_first, new_last)
        for user in qs.iterator():
            new_first = normalisasi_nama(user.first_name) or ''
            new_last = normalisasi_nama(user.last_name) or ''
            
            if user.first_name != new_first or user.last_name != new_last:
                changes.append((user, user.first_name, user.last_name, new_first, new_last))
        
        n_changes = len(changes)
        n_unchanged = total - n_changes
        
        if n_changes == 0:
            self.stdout.write(self.style.SUCCESS(
                f'Semua {total} user sudah ter-normalize. Tidak ada perubahan.'
            ))
            return
        
        # Tampilkan preview
        self.stdout.write(self.style.MIGRATE_LABEL(
            f'Akan ada {n_changes} perubahan ({n_unchanged} user sudah ter-normalize):'
        ))
        self.stdout.write('')
        self.stdout.write(f'{"USERNAME":<30} {"BEFORE":<35} {"AFTER":<35}')
        self.stdout.write('-' * 100)
        
        for user, old_f, old_l, new_f, new_l in changes:
            old_full = f'{old_f} {old_l}'.strip()
            new_full = f'{new_f} {new_l}'.strip()
            self.stdout.write(f'{user.username:<30} {old_full:<35} {new_full:<35}')
        
        self.stdout.write('')
        
        # Apply jika diminta
        if not apply_changes:
            self.stdout.write(self.style.WARNING(
                f'\nDRY-RUN selesai. Untuk benar-benar apply, jalankan ulang dengan flag --apply\n'
            ))
            return
        
        # APPLY mode — wrap dalam atomic
        self.stdout.write(self.style.MIGRATE_HEADING('Menyimpan perubahan ke DB...'))
        with transaction.atomic():
            for user, _, _, new_f, new_l in changes:
                user.first_name = new_f
                user.last_name = new_l
                user.save(update_fields=['first_name', 'last_name'])
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Selesai. {n_changes} user ter-update.\n'
        ))