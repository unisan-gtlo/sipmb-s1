import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from .models import User
from .forms import RegistrasiAwalForm, LoginForm
from master.models import GelombangPenerimaan, ProdiPMB
from pendaftaran.models import Pendaftaran, ProfilPendaftar, TokenAktivasi

logger = logging.getLogger(__name__)


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