import logging
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from utils.sso_client import verify_sso_token

logger = logging.getLogger(__name__)
User = get_user_model()


class SSOAutoLoginMiddleware:
    """
    Middleware yang auto-login user berdasarkan SSO cookie.
    Hanya berlaku untuk user SSO (admin, operator, pimpinan, panitia).
    Calon maba dan recruiter login langsung ke SIPMB (bukan SSO).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lewati jika user sudah login
        if not request.user.is_authenticated:
            sso_token = request.COOKIES.get('sso_token')
            if sso_token:
                self._auto_login(request, sso_token)

        response = self.get_response(request)
        return response

    def _auto_login(self, request, token):
        try:
            data = verify_sso_token(token)
            if not data or not data.get('valid'):
                return

            user_data = data.get('user', {})
            username  = user_data.get('username')
            role      = user_data.get('role', '')
            sso_uuid  = user_data.get('uuid', '')

            # Hanya proses role yang valid untuk SSO login
            sso_roles = ['admin', 'admin_pmb', 'operator_pmb',
                         'panitia_seleksi', 'pimpinan']
            if role not in sso_roles:
                return

            # Map role SSO ke role SIPMB
            role_map = {
                'admin':          'admin_pmb',
                'admin_pmb':      'admin_pmb',
                'operator_pmb':   'operator_pmb',
                'panitia_seleksi':'panitia_seleksi',
                'pimpinan':       'pimpinan',
            }
            sipmb_role = role_map.get(role, 'operator_pmb')

            profil    = user_data.get('profil', {})
            nama      = profil.get('nama_lengkap', '')
            nama_list = nama.split(' ', 1)
            first     = nama_list[0] if nama_list else username
            last      = nama_list[1] if len(nama_list) > 1 else ''

            # Buat atau update user lokal berdasarkan SSO
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email':        user_data.get('email', ''),
                    'first_name':   first,
                    'last_name':    last,
                    'role':         sipmb_role,
                    'is_sso_user':  True,
                    'sso_uuid':     sso_uuid,
                    'is_staff':     sipmb_role == 'admin_pmb',
                    'is_superuser': sipmb_role == 'admin_pmb',
                }
            )

            if not created:
                # Update data terbaru dari SSO
                user.email       = user_data.get('email', user.email)
                user.first_name  = first
                user.last_name   = last
                user.role        = sipmb_role
                user.is_sso_user = True
                user.sso_uuid    = sso_uuid
                user.save(update_fields=[
                    'email', 'first_name', 'last_name',
                    'role', 'is_sso_user', 'sso_uuid'
                ])

            # Login user ke Django session
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f'SSO auto-login: {username} ({sipmb_role})')

        except Exception as e:
            logger.error(f'SSO middleware error: {e}')