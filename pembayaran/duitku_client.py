# pembayaran/duitku_client.py
"""
Client wrapper untuk Duitku Payment Gateway API.
Dokumentasi: https://docs.duitku.com/api/id/
"""
import hashlib
import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


# ==================== ENDPOINT URLS ====================
SANDBOX_BASE_URL = "https://sandbox.duitku.com/webapi/api"
PRODUCTION_BASE_URL = "https://passport.duitku.com/webapi/api"


def _get_config():
    """Ambil kredensial Duitku dari PengaturanSistem."""
    from master.models import PengaturanSistem
    p = PengaturanSistem.get()
    if not p:
        raise ValueError("PengaturanSistem tidak ditemukan")

    merchant_code = p.duitku_merchant_code or ''
    api_key = p.duitku_api_key or ''
    is_sandbox = p.duitku_sandbox

    if not merchant_code or not api_key:
        raise ValueError(
            "Duitku credentials belum di-set. "
            "Isi merchant_code & api_key di /admin/master/pengaturansistem/"
        )

    base_url = SANDBOX_BASE_URL if is_sandbox else PRODUCTION_BASE_URL
    return {
        'merchant_code': merchant_code.strip(),
        'api_key': api_key.strip(),
        'is_sandbox': is_sandbox,
        'base_url': base_url,
    }


def _md5(text: str) -> str:
    """MD5 hash helper — Duitku pakai MD5 untuk signature."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


# ==================== REQUEST TRANSACTION ====================
def request_transaction(tagihan, return_url: str, callback_url: str, payment_method: str = 'VC'):
    """
    Initiate transaksi baru ke Duitku.

    Args:
        tagihan: instance pembayaran.Tagihan
        return_url: URL browser setelah user selesai bayar
        callback_url: URL webhook Duitku POST status ke SIPMB

    Returns:
        dict: {
            'success': bool,
            'merchant_order_id': str,
            'reference': str (Duitku reference id),
            'payment_url': str (URL untuk redirect atau embed Pop),
            'va_number': str (kalau method VA),
            'raw': dict (full response dari Duitku),
        }
    """
    cfg = _get_config()

    pendaftaran = tagihan.pendaftaran
    user = pendaftaran.user

    # Merchant Order ID — harus unique per transaksi
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    merchant_order_id = f"{tagihan.kode_bayar}-{timestamp_ms}"[:50]

    amount = int(tagihan.jumlah)

    # Signature: md5(merchantCode + merchantOrderId + paymentAmount + apiKey)
    signature = _md5(
        f"{cfg['merchant_code']}{merchant_order_id}{amount}{cfg['api_key']}"
    )

    nama_customer = (
        user.get_full_name()
        or getattr(pendaftaran, 'nama_lengkap', None)
        or user.email
    )
    nama_parts = nama_customer.split(' ', 1)
    first_name = nama_parts[0]
    last_name = nama_parts[1] if len(nama_parts) > 1 else '-'

    # Default phone — format Duitku: 08xx/628xx
    phone = (getattr(user, 'no_hp', '') or '').strip()
    if not phone:
        phone = '08000000000'

    payload = {
        'merchantCode': cfg['merchant_code'],
        'paymentAmount': amount,
        'paymentMethod': payment_method,
        'merchantOrderId': merchant_order_id,
        'productDetails': f"Biaya Pendaftaran PMB UNISAN - {tagihan.kode_bayar}",
        'email': user.email,
        'phoneNumber': phone,
        'customerVaName': nama_customer[:20],
        'callbackUrl': callback_url,
        'returnUrl': return_url,
        'signature': signature,
        'expiryPeriod': 60 * 24,  # menit — 24 jam

        'customerDetail': {
            'firstName': first_name[:50],
            'lastName': last_name[:50],
            'email': user.email,
            'phoneNumber': phone,
            'billingAddress': {
                'firstName': first_name[:50],
                'lastName': last_name[:50],
                'address': '-',
                'city': 'Gorontalo',
                'postalCode': '96128',
                'phone': phone,
                'countryCode': 'ID',
            },
        },

        'itemDetails': [{
            'name': f"Biaya Pendaftaran PMB - {tagihan.get_jenis_display()}",
            'price': amount,
            'quantity': 1,
        }],
    }

    url = f"{cfg['base_url']}/merchant/v2/inquiry"
    logger.info(f"Duitku request: orderId={merchant_order_id} amount={amount}")

    response = requests.post(
        url,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=20,
    )

    try:
        data = response.json()
    except ValueError:
        logger.error(f"Duitku non-JSON response: {response.status_code} {response.text[:200]}")
        return {
            'success': False,
            'error': f'Duitku mengembalikan response tidak valid (HTTP {response.status_code})',
            'raw': response.text[:500],
        }

    logger.info(f"Duitku response: status={data.get('statusCode')} msg={data.get('statusMessage')}")

    if data.get('statusCode') == '00':
        return {
            'success': True,
            'merchant_order_id': merchant_order_id,
            'reference': data.get('reference', ''),
            'payment_url': data.get('paymentUrl', ''),
            'va_number': data.get('vaNumber', ''),
            'raw': data,
        }
    else:
        return {
            'success': False,
            'error': data.get('statusMessage', 'Unknown error from Duitku'),
            'status_code': data.get('statusCode'),
            'raw': data,
        }


# ==================== CHECK TRANSACTION STATUS ====================
def check_transaction_status(merchant_order_id: str):
    """
    Cek status transaksi di Duitku.

    Returns:
        dict: {
            'success': bool,
            'status': 'paid'/'pending'/'failed'/'unknown',
            'raw': dict (full response),
        }
    """
    cfg = _get_config()

    # Signature: md5(merchantCode + merchantOrderId + apiKey)
    signature = _md5(
        f"{cfg['merchant_code']}{merchant_order_id}{cfg['api_key']}"
    )

    payload = {
        'merchantCode': cfg['merchant_code'],
        'merchantOrderId': merchant_order_id,
        'signature': signature,
    }

    url = f"{cfg['base_url']}/merchant/transactionStatus"

    response = requests.post(
        url,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=15,
    )

    try:
        data = response.json()
    except ValueError:
        return {
            'success': False,
            'error': 'Invalid response from Duitku',
            'raw': response.text[:500],
        }

    # Duitku statusCode: 00=paid, 01=pending, 02=failed
    code = data.get('statusCode', '')
    status_map = {
        '00': 'paid',
        '01': 'pending',
        '02': 'failed',
    }

    return {
        'success': True,
        'status': status_map.get(code, 'unknown'),
        'amount': data.get('amount', 0),
        'reference': data.get('reference', ''),
        'raw': data,
    }


# ==================== VERIFY CALLBACK SIGNATURE ====================
def verify_callback_signature(merchant_code: str, amount: str,
                              merchant_order_id: str, signature: str) -> bool:
    """
    Verifikasi signature dari Duitku callback.
    Formula: md5(merchantCode + amount + merchantOrderId + apiKey)
    """
    cfg = _get_config()

    if merchant_code != cfg['merchant_code']:
        logger.warning(
            f"Duitku callback merchant mismatch: got={merchant_code} expected={cfg['merchant_code']}"
        )
        return False

    expected = _md5(f"{merchant_code}{amount}{merchant_order_id}{cfg['api_key']}")
    return expected == signature