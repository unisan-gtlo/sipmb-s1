import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_sso_token(token: str) -> dict | None:
    """
    Verifikasi token JWT ke Portal SSO.
    Return data user jika valid, None jika tidak valid.
    """
    try:
        sso_url    = getattr(settings, 'SSO_BASE_URL', '')
        secret_key = getattr(settings, 'SSO_SECRET_KEY', '')

        if not sso_url or not secret_key:
            # SSO belum dikonfigurasi — skip (mode development)
            return None

        response = requests.post(
            f'{sso_url}/api/verify-token/',
            json={'token': token},
            headers={'Authorization': f'Bearer {secret_key}'},
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        return None

    except requests.exceptions.ConnectionError:
        # SSO server tidak bisa dihubungi (normal saat development lokal)
        logger.warning('SSO server tidak bisa dihubungi — skip auto-login')
        return None
    except Exception as e:
        logger.error(f'SSO verify token error: {e}')
        return None
