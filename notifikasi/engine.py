import logging
import re
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context

from .models import TemplateNotifikasi, LogNotifikasi

logger = logging.getLogger(__name__)


def render_template(teks, data):
    """Render template dengan data dinamis menggunakan {{variabel}}"""
    for key, value in data.items():
        teks = teks.replace(f'{{{{{key}}}}}', str(value) if value else '')
    return teks


def get_data_pendaftaran(pendaftaran):
    """Ambil data untuk template notifikasi"""
    try:
        profil = pendaftaran.profil
        nama   = profil.pendaftaran.user.get_full_name()
    except:
        nama = pendaftaran.user.get_full_name()

    return {
        'nama':            nama,
        'no_pendaftaran':  pendaftaran.no_pendaftaran,
        'jalur':           pendaftaran.jalur.nama_jalur,
        'gelombang':       pendaftaran.gelombang.nama_gelombang,
        'prodi':           pendaftaran.prodi_pilihan_1.nama_prodi,
        'status':          pendaftaran.get_status_display(),
        'email':           pendaftaran.user.email,
        'no_hp':           pendaftaran.user.no_hp or '',
        'url_dashboard':   f'{settings.BASE_URL}/dashboard/',
        'tahun_akademik':  '2025/2026',
        'nama_kampus':     'Universitas Ichsan Gorontalo (UNISAN)',
        'kontak_pmb':      getattr(settings, 'WHATSAPP_PMB', ''),
    }


def kirim_email(user, subjek, isi, pendaftaran=None, template=None):
    """Kirim email notifikasi"""
    log = LogNotifikasi(
        user=user, pendaftaran=pendaftaran,
        template=template, jenis='email',
        tujuan=user.email, subjek=subjek, isi=isi
    )
    try:
        send_mail(
            subject      = subjek,
            message      = isi,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [user.email],
            fail_silently = False,
        )
        log.status = 'terkirim'
        log.save()
        return True
    except Exception as e:
        log.status    = 'gagal'
        log.error_msg = str(e)
        log.save()
        logger.error(f'Error kirim email ke {user.email}: {e}')
        return False


def kirim_whatsapp(no_hp, pesan, user, pendaftaran=None, template=None):
    """
    Kirim WhatsApp via Fonnte API
    Set FONNTE_TOKEN di settings/.env
    """
    log = LogNotifikasi(
        user=user, pendaftaran=pendaftaran,
        template=template, jenis='whatsapp',
        tujuan=no_hp, isi=pesan
    )

    token = getattr(settings, 'FONNTE_TOKEN', '')
    if not token:
        log.status    = 'gagal'
        log.error_msg = 'FONNTE_TOKEN belum dikonfigurasi'
        log.save()
        return False

    # Bersihkan nomor HP
    no_hp = re.sub(r'[^0-9]', '', no_hp)
    if no_hp.startswith('0'):
        no_hp = '62' + no_hp[1:]
    elif not no_hp.startswith('62'):
        no_hp = '62' + no_hp

    try:
        import urllib.request
        import urllib.parse
        import json

        data = urllib.parse.urlencode({
            'target':  no_hp,
            'message': pesan,
        }).encode()

        req = urllib.request.Request(
            'https://api.fonnte.com/send',
            data=data,
            headers={
                'Authorization': token,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get('status'):
                log.status = 'terkirim'
                log.save()
                return True
            else:
                log.status    = 'gagal'
                log.error_msg = str(result)
                log.save()
                return False

    except Exception as e:
        log.status    = 'gagal'
        log.error_msg = str(e)
        log.save()
        logger.error(f'Error kirim WA ke {no_hp}: {e}')
        return False


def kirim_notifikasi(trigger, pendaftaran):
    """
    Fungsi utama — kirim notifikasi berdasarkan trigger
    Dipanggil dari views saat ada perubahan status
    """
    try:
        template = TemplateNotifikasi.objects.get(trigger=trigger, aktif=True)
    except TemplateNotifikasi.DoesNotExist:
        return False

    data = get_data_pendaftaran(pendaftaran)
    user = pendaftaran.user

    hasil = True

    # Kirim Email
    if template.jenis in ['email', 'both'] and template.subjek_email:
        subjek = render_template(template.subjek_email, data)
        isi    = render_template(template.isi_email, data)
        hasil = kirim_email(user, subjek, isi, pendaftaran, template)

    # Kirim WhatsApp
    if template.jenis in ['whatsapp', 'both'] and template.isi_wa:
        no_hp = user.no_hp
        if no_hp:
            pesan = render_template(template.isi_wa, data)
            kirim_whatsapp(no_hp, pesan, user, pendaftaran, template)

    return hasil


def kirim_notifikasi_manual(pendaftaran_list, subjek, isi_email, isi_wa='', kirim_ke='both'):
    """Kirim notifikasi massal manual dari admin"""
    berhasil = 0
    gagal    = 0

    for p in pendaftaran_list:
        user = p.user
        data = get_data_pendaftaran(p)

        if kirim_ke in ['email', 'both'] and isi_email:
            subj = render_template(subjek, data)
            isi  = render_template(isi_email, data)
            if kirim_email(user, subj, isi, p):
                berhasil += 1
            else:
                gagal += 1

        if kirim_ke in ['whatsapp', 'both'] and isi_wa and user.no_hp:
            pesan = render_template(isi_wa, data)
            kirim_whatsapp(user.no_hp, pesan, user, p)

    return berhasil, gagal