import logging
import anthropic
from django.conf import settings
from .models import KnowledgeBase, PengaturanChatbot, SesiChat, RiwayatChat

logger = logging.getLogger(__name__)


def cari_knowledge_base(pesan: str) -> KnowledgeBase | None:
    """
    Cari jawaban di knowledge base berdasarkan kata kunci.
    Return KnowledgeBase jika ada match, None jika tidak.
    """
    pesan_lower = pesan.lower()
    kb_list = KnowledgeBase.objects.filter(status='aktif').order_by('urutan_prioritas')

    for kb in kb_list:
        kata_kunci = [k.strip().lower() for k in kb.kata_kunci.split(',') if k.strip()]
        for kata in kata_kunci:
            if kata and kata in pesan_lower:
                return kb
    return None


def get_context_pmb() -> str:
    """Ambil konteks dinamis dari database SIPMB untuk dikirim ke AI"""
    from master.models import JalurPenerimaan, GelombangPenerimaan, PengaturanSistem
    try:
        pengaturan = PengaturanSistem.get()
        jalur_list = JalurPenerimaan.objects.filter(status='aktif')
        gelombang_list = GelombangPenerimaan.objects.filter(status='buka')

        jalur_text = '\n'.join([
            f'- {j.nama_jalur} ({j.kode_jalur}): {j.deskripsi[:100] if j.deskripsi else ""}'
            for j in jalur_list
        ])

        gelombang_text = '\n'.join([
            f'- {g.nama_gelombang} ({g.jalur.nama_jalur}): '
            f'buka {g.tgl_buka} s.d. {g.tgl_tutup}, '
            f'biaya Rp {g.biaya_akhir:,.0f}'
            for g in gelombang_list
        ])

        return f"""
INFORMASI PMB UNISAN YANG AKTIF SAAT INI:

Tahun Akademik: {pengaturan.tahun_akademik_aktif}
Status Pendaftaran: {pengaturan.get_status_pendaftaran_display()}
Kontak WA PMB: {pengaturan.whatsapp_pmb}
Email PMB: {pengaturan.email_pmb}

JALUR PENERIMAAN AKTIF:
{jalur_text if jalur_text else 'Belum ada jalur aktif'}

GELOMBANG YANG SEDANG BUKA:
{gelombang_text if gelombang_text else 'Belum ada gelombang yang buka saat ini'}
"""
    except Exception as e:
        logger.error(f'Error get_context_pmb: {e}')
        return 'Informasi PMB UNISAN - Universitas Ichsan Gorontalo'


def tanya_claude(pesan: str, riwayat: list, pengaturan: PengaturanChatbot) -> str:
    """Kirim pertanyaan ke Claude AI dan dapatkan jawaban"""
    try:
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return pengaturan.pesan_fallback

        client = anthropic.Anthropic(api_key=api_key)

        # System prompt
        system_prompt = pengaturan.system_prompt or f"""
Kamu adalah {pengaturan.nama_bot}, asisten virtual Penerimaan Mahasiswa Baru (PMB) 
Universitas Ichsan Gorontalo (UNISAN).

{get_context_pmb()}

ATURAN:
1. Jawab HANYA pertanyaan seputar PMB dan UNISAN
2. Gunakan bahasa Indonesia yang ramah dan sopan
3. Jawaban singkat, padat, dan jelas (maks 3-4 kalimat)
4. Jika tidak tahu, sarankan hubungi panitia PMB
5. Jangan menjawab pertanyaan di luar konteks PMB/UNISAN
6. Sertakan nomor WA panitia jika pertanyaan butuh konfirmasi
"""
        # Bangun history percakapan
        messages = []
        for r in riwayat[-6:]:  # Ambil 6 pesan terakhir
            messages.append({
                'role': 'user' if r['pengirim'] == 'user' else 'assistant',
                'content': r['pesan']
            })
        messages.append({'role': 'user', 'content': pesan})

        response = client.messages.create(
            model=pengaturan.ai_model,
            max_tokens=pengaturan.max_token,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    except anthropic.AuthenticationError:
        logger.error('Anthropic API key tidak valid')
        return pengaturan.pesan_fallback
    except Exception as e:
        logger.error(f'Error tanya_claude: {e}')
        return pengaturan.pesan_fallback


def proses_pesan(session_id: str, pesan: str, user=None, nama_tamu: str = '', ip: str = '') -> dict:
    """
    Proses pesan dari user — cek KB dulu, lalu AI jika tidak ada di KB.
    Return: {jawaban, sumber, session_id}
    """
    pengaturan = PengaturanChatbot.get()

    # Cek apakah chatbot aktif
    if not pengaturan.aktif:
        return {
            'jawaban':    pengaturan.pesan_diluar_jam,
            'sumber':     'fallback',
            'session_id': session_id,
        }

    # Ambil atau buat sesi chat
    sesi, _ = SesiChat.objects.get_or_create(
        session_id=session_id,
        defaults={
            'user':       user if user and user.is_authenticated else None,
            'nama_tamu':  nama_tamu,
            'ip_address': ip or None,
        }
    )

    # Simpan pesan user
    RiwayatChat.objects.create(
        sesi=sesi, pengirim='user', pesan=pesan
    )
    sesi.total_pesan += 1
    sesi.save(update_fields=['total_pesan', 'tgl_terakhir'])

    # Ambil riwayat untuk konteks AI
    riwayat = list(sesi.pesan.values('pengirim', 'pesan').order_by('-tgl_kirim')[:10])
    riwayat.reverse()

    # 1. Cek knowledge base dulu
    kb_match = cari_knowledge_base(pesan)
    if kb_match:
        jawaban = kb_match.jawaban
        if kb_match.link_terkait:
            jawaban += f'\n\nInfo lebih lanjut: {kb_match.link_terkait}'
        sumber  = 'knowledge_base'
        RiwayatChat.objects.create(
            sesi=sesi, pengirim='bot',
            pesan=jawaban, sumber_jawaban='knowledge_base',
            knowledge_base=kb_match
        )
    else:
        # 2. Tanya Claude AI
        jawaban = tanya_claude(pesan, riwayat, pengaturan)
        sumber  = 'ai'
        RiwayatChat.objects.create(
            sesi=sesi, pengirim='bot',
            pesan=jawaban, sumber_jawaban='ai'
        )

    sesi.total_pesan += 1
    sesi.save(update_fields=['total_pesan', 'tgl_terakhir'])

    return {
        'jawaban':    jawaban,
        'sumber':     sumber,
        'session_id': session_id,
    }