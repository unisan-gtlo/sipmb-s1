# pembayaran/management/commands/backfill_tagihan.py
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from pendaftaran.models import Pendaftaran
from pembayaran.models import Tagihan


class Command(BaseCommand):
    help = (
        "Generate Tagihan 'biaya_pendaftaran' untuk semua Pendaftaran "
        "yang belum punya tagihan. Aman dijalankan berkali-kali (idempoten)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview saja, tanpa commit ke DB.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        total = dibuat = lunas_auto = dilewati = gelombang_kosong = 0

        qs = Pendaftaran.objects.select_related('gelombang').order_by('id')
        self.stdout.write(self.style.HTTP_INFO(
            f"Total Pendaftaran di DB: {qs.count()}"
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING(">>> MODE DRY-RUN — tidak ada data disimpan\n"))

        with transaction.atomic():
            for p in qs:
                total += 1

                # Skip kalau sudah punya tagihan biaya_pendaftaran
                if Tagihan.objects.filter(
                    pendaftaran=p,
                    jenis='biaya_pendaftaran',
                ).exists():
                    dilewati += 1
                    continue

                gel = p.gelombang
                if not gel:
                    self.stdout.write(self.style.WARNING(
                        f"  [SKIP] {p.no_pendaftaran}: gelombang kosong"
                    ))
                    gelombang_kosong += 1
                    continue

                jumlah = gel.biaya_akhir or gel.biaya_penuh or Decimal('0')
                status = 'lunas' if jumlah == 0 else 'belum_bayar'

                self.stdout.write(
                    f"  {p.no_pendaftaran} | {gel.nama_gelombang} | "
                    f"Rp {jumlah:,.0f} → {status}"
                )

                if not dry_run:
                    Tagihan.objects.create(
                        pendaftaran=p,
                        jenis='biaya_pendaftaran',
                        jumlah=jumlah,
                        status=status,
                        catatan='Backfill tagihan untuk pendaftar existing.',
                    )

                dibuat += 1
                if status == 'lunas':
                    lunas_auto += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Selesai. Total: {total} | Dibuat: {dibuat} "
            f"(lunas-auto: {lunas_auto}) | Dilewati: {dilewati} | "
            f"Gelombang kosong: {gelombang_kosong}"
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "Dry-run — rerun tanpa --dry-run untuk commit."
            ))