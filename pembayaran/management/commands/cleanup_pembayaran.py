"""
Management command untuk auto-cleanup pembayaran yang stuck.

Tujuan:
- Mark TransaksiDuitku 'pending' yang sudah lewat batas waktu sebagai 'expired'
- Reset Tagihan dengan status 'menunggu_pembayaran' kembali ke 'belum_bayar'
  jika tidak ada transaksi aktif lain

Cara pakai:
    python manage.py cleanup_pembayaran                   # default 60 menit
    python manage.py cleanup_pembayaran --minutes 30      # custom timeout
    python manage.py cleanup_pembayaran --dry-run         # preview tanpa aksi nyata
    python manage.py cleanup_pembayaran --verbose         # log detail per tagihan

Best practice scheduling:
- Jalankan tiap 30 menit via cron/Task Scheduler
- Timeout >= 60 menit (lebih lama dari standard timeout VA Duitku 24 jam)
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pembayaran.models import Tagihan, TransaksiDuitku

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Cleanup tagihan stuck di status 'menunggu_pembayaran' yang transaksinya "
        "tidak diselesaikan dalam batas waktu tertentu."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=60,
            help='Batas waktu (menit) sebelum transaksi pending dianggap expired. Default: 60.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview tanpa modifikasi database.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Log detail per tagihan/transaksi yang diproses.',
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        dry_run = options['dry_run']
        verbose = options['verbose']

        cutoff = timezone.now() - timedelta(minutes=minutes)

        # Header
        mode_label = "DRY-RUN (preview)" if dry_run else "LIVE"
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n{'=' * 70}\n"
            f" CLEANUP PEMBAYARAN STUCK [{mode_label}]\n"
            f"{'=' * 70}"
        ))
        self.stdout.write(f" Waktu sekarang  : {timezone.now()}")
        self.stdout.write(f" Batas waktu     : {minutes} menit")
        self.stdout.write(f" Cutoff datetime : {cutoff}")
        self.stdout.write("")

        # ---------- 1. Cari TransaksiDuitku pending yang sudah expired ----------
        pending_txs = TransaksiDuitku.objects.filter(
            status='pending',
            created_at__lt=cutoff,
        ).select_related('tagihan')

        total_pending = pending_txs.count()
        self.stdout.write(f"[1] TransaksiDuitku pending > {minutes} menit: {total_pending}")

        if total_pending == 0:
            self.stdout.write(self.style.SUCCESS("    Tidak ada transaksi yang perlu di-cleanup."))
            self.stdout.write("")
            return

        # ---------- 2. Process per transaksi ----------
        expired_count = 0
        rollback_count = 0
        skipped_count = 0

        for tx in pending_txs:
            tagihan = tx.tagihan
            age_minutes = (timezone.now() - tx.created_at).total_seconds() / 60

            if verbose:
                self.stdout.write(
                    f"\n  -> {tx.merchant_order_id}"
                    f"\n     Tagihan : {tagihan.kode_bayar} (status: {tagihan.status})"
                    f"\n     Method  : {tx.payment_method}"
                    f"\n     Age     : {age_minutes:.1f} menit"
                )

            if dry_run:
                # Preview only — hitung saja, tidak modifikasi
                expired_count += 1
                if tagihan.status == 'menunggu_pembayaran':
                    # Cek apakah ada transaksi pending lain yang masih dalam batas waktu
                    has_other_active = (
                        tagihan.transaksi_duitku
                        .exclude(pk=tx.pk)
                        .filter(status__in=('pending', 'paid'), created_at__gte=cutoff)
                        .exists()
                    )
                    if not has_other_active:
                        rollback_count += 1
                continue

            # LIVE — atomic update
            with transaction.atomic():
                # Mark transaksi sebagai expired
                tx.status = 'expired'
                tx.save(update_fields=['status', 'updated_at'])
                expired_count += 1

                # Cek apakah masih ada transaksi pending/paid LAIN yang aktif
                has_other_active = (
                    tagihan.transaksi_duitku
                    .exclude(pk=tx.pk)
                    .filter(status__in=('pending', 'paid'))
                    .exists()
                )

                # Rollback tagihan kalau:
                # - Status saat ini 'menunggu_pembayaran' (artinya stuck karena Duitku)
                # - Tidak ada transaksi lain yang aktif
                if not has_other_active and tagihan.status == 'menunggu_pembayaran':
                    old_status = tagihan.status
                    tagihan.status = 'belum_bayar'
                    tagihan.catatan = (
                        f"{tagihan.catatan or ''}\n"
                        f"[AUTO-CLEANUP {timezone.now().date()}] "
                        f"Status di-rollback dari '{old_status}' ke 'belum_bayar' "
                        f"karena transaksi {tx.merchant_order_id} expired (>{minutes} menit)."
                    ).strip()
                    tagihan.save(update_fields=['status', 'catatan', 'updated_at'])
                    rollback_count += 1
                    logger.info(
                        f"Cleanup rolled back tagihan {tagihan.kode_bayar} to belum_bayar "
                        f"(expired tx: {tx.merchant_order_id})"
                    )
                else:
                    skipped_count += 1
                    if verbose:
                        self.stdout.write(
                            f"     [SKIP] Tagihan tidak di-rollback "
                            f"(status='{tagihan.status}', has_other_active={has_other_active})"
                        )

        # ---------- 3. Summary ----------
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"{'=' * 70}\n SUMMARY\n{'=' * 70}"))
        self.stdout.write(f" Transaksi expired (mark 'expired')       : {expired_count}")
        self.stdout.write(f" Tagihan di-rollback ('belum_bayar')      : {rollback_count}")
        self.stdout.write(f" Tagihan tidak di-rollback (skip)         : {skipped_count}")

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                " *** DRY-RUN: Tidak ada perubahan database. ***\n"
                " *** Jalankan tanpa --dry-run untuk eksekusi nyata. ***"
            ))
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(" Cleanup selesai."))
        self.stdout.write("")