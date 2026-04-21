import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django_ratelimit.decorators import ratelimit

from .models import User
from .forms import RegistrasiAwalForm, LoginForm
from master.models import GelombangPenerimaan, ProdiPMB
from pendaftaran.models import Pendaftaran, ProfilPendaftar, TokenAktivasi
from konten.models import Pengumuman, Testimoni, MitraKerjasama, MediaSosial, DokumenDownload, BrosurFakultas, FAQ

# ============================================================
# MASTER WARNA FAKULTAS — dipakai di:
# - Halaman beranda publik (section Fakultas & Prodi)
# - Halaman publik /prodi/
# - Dashboard admin PMB (grafik pendaftar per prodi)
# Kode fakultas harus sama persis dengan kode_fakultas di SIMDA.
# ============================================================
WARNA_FAKULTAS = {
    'FK':    {
        'gradient': 'linear-gradient(135deg,#1d4ed8,#3b82f6)',
        'light': '#dbeafe', 'text': '#1d4ed8',
        'icon': 'laptop'
    },
    'FE':    {
        'gradient': 'linear-gradient(135deg,#b45309,#f59e0b)',
        'light': '#fef3c7', 'text': '#b45309',
        'icon': 'graph-up-arrow'
    },
    'FP':    {
        'gradient': 'linear-gradient(135deg,#15803d,#22c55e)',
        'light': '#dcfce7', 'text': '#15803d',
        'icon': 'tree'
    },
    'FH':    {
        'gradient': 'linear-gradient(135deg,#b91c1c,#ef4444)',
        'light': '#fee2e2', 'text': '#b91c1c',
        'icon': 'briefcase'
    },
    'FISIP': {
        'gradient': 'linear-gradient(135deg,#6d28d9,#a78bfa)',
        'light': '#ede9fe', 'text': '#6d28d9',
        'icon': 'people'
    },
    'FT':    {
        'gradient': 'linear-gradient(135deg,#c2410c,#f97316)',
        'light': '#ffedd5', 'text': '#c2410c',
        'icon': 'gear'
    },
    'S2':    {
        'gradient': 'linear-gradient(135deg,#0f766e,#14b8a6)',
        'light': '#ccfbf1', 'text': '#0f766e',
        'icon': 'mortarboard'
    },
}

WARNA_FALLBACK = {
    'gradient': 'linear-gradient(135deg,#64748b,#94a3b8)',
    'light': '#f1f5f9', 'text': '#475569',
    'icon': 'building'
}


def warna_fakultas(kode_fakultas):
    """Ambil dict warna berdasarkan kode fakultas. Fallback abu-abu."""
    if not kode_fakultas:
        return WARNA_FALLBACK
    return WARNA_FAKULTAS.get(kode_fakultas.upper(), WARNA_FALLBACK)

logger = logging.getLogger(__name__)

@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def registrasi(request):
    """Halaman registrasi awal calon maba"""
    # Ambil kode referral dari URL jika ada
    kode_ref = request.GET.get('ref', '')

    if request.method == 'POST':
        form = RegistrasiAwalForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data

                # Buat username dari email
                email    = data['email']
                username = email.split('@')[0]

                # Pastikan username unik
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f'{base_username}{counter}'
                    counter += 1

                # Pisah nama lengkap
                nama    = data['nama_lengkap'].strip()
                parts   = nama.split(' ', 1)
                first   = parts[0]
                last    = parts[1] if len(parts) > 1 else ''

                # Buat user baru (belum aktif)
                user = User.objects.create_user(
                    username   = username,
                    email      = email,
                    password   = data['password'],
                    first_name = first,
                    last_name  = last,
                    no_hp      = data['no_hp'],
                    role       = 'calon_maba',
                    is_active  = False,  # belum aktif sampai verifikasi email
                )

                # Buat pendaftaran
                pendaftaran = Pendaftaran.objects.create(
                    user            = user,
                    jalur           = data['jalur'],
                    gelombang       = data['gelombang'],
                    prodi_pilihan_1 = data['prodi_pilihan_1'],
                    prodi_pilihan_2 = data.get('prodi_pilihan_2'),
                    kode_referral   = data.get('kode_referral', ''),
                    kode_voucher    = data.get('kode_voucher', ''),
                    status          = 'DRAFT',
                )

                # Buat profil kosong
                ProfilPendaftar.objects.create(pendaftaran=pendaftaran)

                # Buat token aktivasi
                token_obj = TokenAktivasi.objects.create(user=user)

                # Kirim email aktivasi
                _kirim_email_aktivasi(request, user, token_obj)

                logger.info(f'Registrasi baru: {email} — {pendaftaran.no_pendaftaran}')

                # Redirect ke halaman sukses
                request.session['email_registrasi'] = email
                return redirect('accounts:registrasi_sukses')

            except Exception as e:
                logger.error(f'Error registrasi: {e}')
                messages.error(request, 'Terjadi kesalahan. Silakan coba lagi.')
    else:
        # Pre-fill kode referral dari URL
        initial = {'kode_referral': kode_ref} if kode_ref else {}
        form    = RegistrasiAwalForm(initial=initial)

    # Di view registrasi, setelah Pendaftaran dibuat, tambahkan:
    kode_ref = request.POST.get('kode_referral', '').strip()
    if kode_ref:
        pendaftaran.kode_referral = kode_ref
        pendaftaran.save()

    return render(request, 'publik/registrasi.html', {
        'form':     form,
        'kode_ref': kode_ref,
    })


def registrasi_sukses(request):
    """Halaman sukses setelah registrasi"""
    email = request.session.get('email_registrasi', '')
    return render(request, 'publik/registrasi_sukses.html', {'email': email})


def aktivasi(request, token):
    """Aktivasi akun via link email"""
    try:
        token_obj = TokenAktivasi.objects.get(token=token, sudah_aktif=False)

        if token_obj.is_expired:
            messages.error(request, 'Link aktivasi sudah expired. Minta link baru.')
            return redirect('accounts:login')

        # Aktifkan user
        user            = token_obj.user
        user.is_active  = True
        user.save()

        # Tandai token sudah dipakai
        token_obj.sudah_aktif = True
        token_obj.tgl_aktif   = timezone.now()
        token_obj.save()

        # Auto login
        login(request, user,
              backend='django.contrib.auth.backends.ModelBackend')

        messages.success(request, f'Akun berhasil diaktifkan! Selamat datang, {user.first_name}.')
        return redirect('accounts:aktivasi_sukses')

    except TokenAktivasi.DoesNotExist:
        messages.error(request, 'Link aktivasi tidak valid atau sudah digunakan.')
        return redirect('accounts:login')


def aktivasi_sukses(request):
    """Halaman sukses aktivasi — tampilkan tombol join WA Group"""
    from master.models import PengaturanSistem
    pengaturan = PengaturanSistem.get()
    return render(request, 'publik/aktivasi_sukses.html', {
        'pengaturan': pengaturan,
    })

@ratelimit(key='ip', rate='10/m', method='POST', block=True) 
def login_view(request):
    """Login untuk calon maba dan recruiter"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user_obj = User.objects.get(email=email)
                user     = authenticate(request, username=user_obj.username, password=password)

                if user:
                    if not user.is_active:
                        messages.warning(request, 'Akun belum diaktifkan. Cek email untuk link aktivasi.')
                    else:
                        login(request, user,
                              backend='django.contrib.auth.backends.ModelBackend')
                        return redirect('dashboard:index')
                else:
                    messages.error(request, 'Email atau password salah.')
            except User.DoesNotExist:
                messages.error(request, 'Email belum terdaftar.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('accounts:login')


def _kirim_email_aktivasi(request, user, token_obj):
    """Helper kirim email aktivasi"""
    try:
        link = request.build_absolute_uri(
            reverse('accounts:aktivasi', args=[str(token_obj.token)])
        )
        send_mail(
            subject = 'Aktivasi Akun PMB UNISAN',
            message = f'''Halo {user.first_name},

Terima kasih telah mendaftar di PMB Universitas Ichsan Gorontalo.

Klik link berikut untuk mengaktifkan akun Anda:
{link}

Link ini berlaku selama 24 jam.

Jika Anda tidak merasa mendaftar, abaikan email ini.

Salam,
Panitia PMB UNISAN
pmb@unisan-g.id
''',
            from_email  = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [user.email],
            fail_silently  = True,
        )
    except Exception as e:
        logger.error(f'Error kirim email aktivasi: {e}')

def beranda(request):
    """Halaman beranda publik"""
    from konten.models import Pengumuman, Testimoni, MitraKerjasama, MediaSosial, DokumenDownload, BrosurFakultas, FAQ
    from master.models import JalurPenerimaan, GelombangPenerimaan, PengaturanSistem
    from utils.simda_reader import get_fakultas, get_program_studi
    from django.utils import timezone

    pengaturan         = PengaturanSistem.get()
    jalur_list         = JalurPenerimaan.objects.filter(status='aktif').order_by('urutan')
    gelombang_aktif    = GelombangPenerimaan.objects.filter(status='buka').select_related('jalur')
    pengumuman_penting = Pengumuman.objects.filter(
        status='aktif', penting=True,
        tgl_tayang__lte=timezone.now().date()
    ).order_by('-tgl_tayang')[:3]
    pengumuman_list    = Pengumuman.objects.filter(
        status='aktif',
        tgl_tayang__lte=timezone.now().date()
    ).order_by('-penting', '-tgl_tayang')[:6]
    testimoni_list     = Testimoni.objects.filter(status='aktif').order_by('urutan')[:9]
    mitra_list         = MitraKerjasama.objects.filter(status='aktif').order_by('urutan')[:12]
    medsos_list        = MediaSosial.objects.filter(status='aktif').order_by('urutan')
    dokumen_list       = DokumenDownload.objects.filter(status='aktif').order_by('urutan')[:4]
    faq_list = FAQ.objects.filter(status='aktif').order_by('urutan')
    # Warna per fakultas
    warna_map = WARNA_FAKULTAS

    try:
        fakultas_raw = get_fakultas()
        prodi_s1     = get_program_studi(jenjang='S1')
        brosur_map   = {b.kode_fakultas: b for b in BrosurFakultas.objects.filter(status='aktif')}

        fakultas_list = []
        for f in fakultas_raw:
            kode       = f['kode_fakultas']
            prodi_list = [p for p in prodi_s1 if p['kode_fakultas'] == kode]

            # Skip fakultas yang tidak punya prodi S1
            if not prodi_list:
                continue

            warna = warna_map.get(kode, {
                'gradient': 'linear-gradient(135deg,#667eea,#764ba2)',
                'light': '#ede9fe', 'text': '#667eea', 'icon': 'building'
            })
            fakultas_list.append({
                'kode_fakultas': kode,
                'nama_fakultas': f['nama_fakultas'],
                'prodi_count':   len(prodi_list),
                'prodi_list':    prodi_list,
                'brosur':        brosur_map.get(kode),
                'warna':         warna,
            })
    except Exception:
        fakultas_list = []

    steps = [
        {'judul': 'Isi data awal',     'sub': 'Nama, email, jalur'},
        {'judul': 'Aktivasi email',     'sub': 'Klik link di email'},
        {'judul': 'Lengkapi profil',    'sub': 'Data diri & dokumen'},
        {'judul': 'Bayar pendaftaran',  'sub': 'Transfer atau QRIS'},
        {'judul': 'Ikuti seleksi',      'sub': 'Tes & pengumuman'},
    ]

    from konten.models import Pengumuman, Testimoni, MitraKerjasama, MediaSosial, DokumenDownload, BrosurFakultas, FAQ

    faq_list = FAQ.objects.filter(status='aktif').order_by('urutan')
    context = {
        'pengaturan':         pengaturan,
        'jalur_list':         jalur_list,
        'gelombang_aktif':    gelombang_aktif,
        'pengumuman_penting': pengumuman_penting,
        'pengumuman_list':    pengumuman_list,
        'testimoni_list':     testimoni_list,
        'mitra_list':         mitra_list,
        'medsos_list':        medsos_list,
        'dokumen_list':       dokumen_list,
        'faq_list':           faq_list,
        'fakultas_list':      fakultas_list,
        'steps':              steps,
        'total_jalur':   jalur_list.count(),
        'total_fakultas': len(fakultas_list),  # otomatis hitung dari list yang sudah difilter S1
        'total_prodi':   sum(f['prodi_count'] for f in fakultas_list),  # jumlah prodi S1 saja
        'status_pmb':    'Buka' if pengaturan.status_pendaftaran == 'buka' else 'Tutup',
    }
    return render(request, 'publik/beranda.html', context)

def pengumuman_detail(request, pk):
    from konten.models import Pengumuman
    from django.shortcuts import get_object_or_404
    p = get_object_or_404(Pengumuman, pk=pk, status='aktif')
    return render(request, 'publik/pengumuman_detail.html', {'p': p})    

@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def registrasi_recruiter(request):
    from django.contrib.auth import login

    if request.user.is_authenticated:
        return redirect('afiliasi:daftar')

    step_list = ['Buat Akun', 'Aktivasi Email', 'Daftar Recruiter', 'Akun Aktif']

    if request.method == 'POST':
        nama       = request.POST.get('nama_lengkap', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        no_hp      = request.POST.get('no_hp', '').strip()
        password   = request.POST.get('password', '')
        konfirmasi = request.POST.get('konfirmasi_password', '')
        pekerjaan  = request.POST.get('pekerjaan', '').strip()
        motivasi   = request.POST.get('motivasi', '').strip()
        foto_selfie= request.FILES.get('foto_selfie')
        foto_ktp   = request.FILES.get('foto_ktp')

        errors = []
        if not nama:         errors.append('Nama lengkap wajib diisi.')
        if not email:        errors.append('Email wajib diisi.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email sudah terdaftar.')
        if len(password) < 8: errors.append('Password minimal 8 karakter.')
        if password != konfirmasi: errors.append('Konfirmasi password tidak cocok.')
        if not foto_selfie:  errors.append('Foto selfie wajib diupload.')
        if not foto_ktp:     errors.append('Foto KTP wajib diupload.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'afiliasi/registrasi_recruiter.html', {
                'step_list': step_list,
                'nama': nama, 'email': email, 'no_hp': no_hp,
                'pekerjaan': pekerjaan, 'motivasi': motivasi,
            })

        # Buat user
        nama_parts = nama.split(' ', 1)
        user = User.objects.create_user(
            username   = email,
            email      = email,
            password   = password,
            first_name = nama_parts[0],
            last_name  = nama_parts[1] if len(nama_parts) > 1 else '',
            no_hp      = no_hp,
            role       = 'recruiter',
            is_active  = False,
        )

        # Simpan foto ke model Recruiter
        from afiliasi.models import Recruiter
        import uuid, re
        nama_bersih = re.sub(r'[^a-zA-Z]', '', nama).upper()[:4]
        kode = f"{nama_bersih}{str(uuid.uuid4())[:4].upper()}"
        rec = Recruiter.objects.create(
            user          = user,
            kode_referral = kode,
            pekerjaan     = pekerjaan,
            catatan       = motivasi,
            status        = 'menunggu',
        )
        if foto_selfie: rec.foto_selfie = foto_selfie; rec.save()
        if foto_ktp:    rec.foto_ktp    = foto_ktp;    rec.save()

        # Kirim email aktivasi
        from accounts.models import TokenAktivasi
        token = TokenAktivasi.objects.create(user=user, token=uuid.uuid4())
        aktivasi_url = f"{request.scheme}://{request.get_host()}/accounts/aktivasi/{token.token}/"
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject    = 'Aktivasi Akun Recruiter PMB UNISAN',
            message    = f'Halo {nama_parts[0]},\n\nKlik link berikut untuk mengaktifkan akun Anda:\n\n{aktivasi_url}\n\nSetelah aktif, login dan lengkapi data rekening Anda.',
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [email],
            fail_silently  = True,
        )

        messages.success(request, f'Akun berhasil dibuat! Cek email {email} untuk aktivasi.')
        return redirect('accounts:registrasi_sukses')

    return render(request, 'afiliasi/registrasi_recruiter.html', {
        'step_list': step_list,
    })