from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# =============================================================
# APLIKASI
# =============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'axes',  
    # Apps SIPMB
    'accounts',
    'master',
    'konten',
    'pendaftaran',
    'dokumen',
    'seleksi',
    'pembayaran',
    'hasil',
    'afiliasi',
    'chatbot',
    'laporan',
    'notifikasi',
    'dashboard',
    'admin_pmb',
    
   
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'csp.middleware.CSPMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'utils.sso_middleware.SSOAutoLoginMiddleware',  # SSO middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',               # Brute force protection
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'master.context_processors.pengaturan_global',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================
# DATABASE — 3 KONEKSI
# =============================================================
DATABASES = {
    # Default: schema pmb (data SIPMB S1)
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'options': '-c search_path=pmb'
        },
    },
    # SIMDA: schema master (read-only, data induk)
    'simda': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'options': '-c search_path=master,public'
        },
    },
    # SSO: schema public (autentikasi)
    'sso': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'options': '-c search_path=public'
        },
    },
}

# =============================================================
# AUTH & AXES
# =============================================================
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # jam
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'

# =============================================================
# PASSWORD VALIDATION
# =============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('email', 'username', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Minimum 8 karakter (bisa dinaikkan ke 10 kalau strict)
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================
# INTERNASIONALISASI
# =============================================================
LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Makassar'
USE_I18N = True
USE_TZ = True

# =============================================================
# STATIC & MEDIA
# =============================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================
# EMAIL
# =============================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='pmb@unisan-g.id')

# =============================================================
# SSO
# =============================================================
SSO_BASE_URL = config('SSO_BASE_URL', default='http://localhost:8001')
SSO_SECRET_KEY = config('SSO_SECRET_KEY', default='')
SSO_SISTEM_KODE = config('SSO_SISTEM_KODE', default='PMB_S1')
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# =============================================================
# DUITKU PAYMENT GATEWAY
# =============================================================
DUITKU_MERCHANT_CODE = config('DUITKU_MERCHANT_CODE', default='')
DUITKU_API_KEY = config('DUITKU_API_KEY', default='')
DUITKU_SANDBOX = config('DUITKU_SANDBOX', default=True, cast=bool)
DUITKU_BASE_URL = 'https://sandbox.duitku.com/webapi/api/merchant' if DUITKU_SANDBOX else 'https://passport.duitku.com/webapi/api/merchant'

# =============================================================
# CLAUDE AI — CHATBOT SINTA
# =============================================================
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')
ANTHROPIC_MODEL = 'claude-sonnet-4-6'

# ============================================================
# ========================== LOGGING =========================
# ============================================================
import os

# Pastikan folder logs ada
LOGS_DIR = BASE_DIR / 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'verbose': {
            'format': '[{asctime}] [{levelname}] [{name}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    
    'handlers': {
        # Log umum aplikasi
        'app_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'sipmb.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        # Log khusus security events
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,  # simpan lebih banyak
            'formatter': 'verbose',
        },
        # Console (untuk development)
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    
    'loggers': {
        # Django core
        'django': {
            'handlers': ['app_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django security events (HTTP 400, 500, CSRF, etc)
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Django request errors
        'django.request': {
            'handlers': ['security_file', 'app_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        # django-axes (brute force protection)
        'axes': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # django-ratelimit
        'django_ratelimit': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # App-specific loggers (custom log dari view kita)
        'sipmb': {
            'handlers': ['app_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sipmb.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ============================================================
# ======================== END LOGGING =======================
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Notifikasi
BASE_URL        = 'http://localhost:8000'  # Ganti dengan domain saat production
FONNTE_TOKEN    = config('FONNTE_TOKEN', default='')
WHATSAPP_PMB    = config('WHATSAPP_PMB', default='')

# Email (sudah ada, pastikan ini ada)
EMAIL_BACKEND   = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST      = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT      = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS   = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='PMB UNISAN <pmb@unisan-g.id>')

# ============================================================
# ===================== SECURITY SETTINGS ====================
# ============================================================
# Aktif hanya saat DEBUG=False (production)
# Reference: https://docs.djangoproject.com/en/5.0/topics/security/

if not DEBUG:
    # --------------------- HTTPS ENFORCEMENT ---------------------
    # Semua traffic harus HTTPS. Ini bekerja bareng dengan Nginx redirect.
    SECURE_SSL_REDIRECT = True
    
    # Proxy header — Nginx kasih tahu Django kalau request aslinya HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # HSTS — force browser selalu pakai HTTPS untuk domain ini
    # Browser akan remember ini selama SECONDS detik
    SECURE_HSTS_SECONDS = 31536000  # 1 tahun
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # --------------------- COOKIE SECURITY ---------------------
    # Cookie hanya dikirim lewat HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Cookie tidak bisa diakses via JavaScript (prevent XSS mencuri cookie)
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # SameSite — prevent CSRF attack via cross-site request
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Session timeout — logout otomatis setelah 2 jam idle
    SESSION_COOKIE_AGE = 7200  # 2 jam dalam detik
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # True = strict (logout saat browser ditutup)
    
    # --------------------- BROWSER SECURITY HEADERS ---------------------
    # X-Content-Type-Options: nosniff
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # Referrer policy — kontrol info referrer yang dikirim ke situs lain
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # Cross-origin policies
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# --------------------- CSRF TRUSTED ORIGINS ---------------------
# Django 4.0+ butuh ini untuk POST request cross-origin
# Berlaku di production maupun development
CSRF_TRUSTED_ORIGINS = [
    'https://pmb.unisan-g.id',
]

# Kalau DEBUG, tambah juga localhost untuk development
if DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

# --------------------- X-FRAME-OPTIONS ---------------------
# Deny iframe embedding (prevent clickjacking)
X_FRAME_OPTIONS = 'DENY'

# --------------------- FILE UPLOAD LIMITS ---------------------
# Batas ukuran upload — prevent server overflow
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # max form fields per request

# --------------------- ADMIN SECURITY ---------------------
# Rename admin URL dari /admin/ ke non-standard
# Tapi kita tidak rename karena Anda sudah familiar dengan /admin/
# Kalau mau rename, ubah di config/urls.py dari path('admin/', ...) 
# ke path('hogwarts-panel/', ...)

# --------------------- LOG SQL INJECTION WARNINGS ---------------------
# Django sudah protected dari SQL injection via ORM,
# tapi kita log kalau ada query aneh

# ============================================================
# =================== END SECURITY SETTINGS ==================
# ============================================================

# ============================================================
# ================= RATE LIMIT CONFIGURATION =================
# ============================================================
# Karena kita pakai Nginx reverse proxy + Unix socket,
# REMOTE_ADDR kosong. Ambil IP dari header X-Forwarded-For
# yang di-set Nginx.
#
# Urutan: cek X-Forwarded-For dulu (standar), fallback ke X-Real-IP

RATELIMIT_IP_META_KEY = 'HTTP_X_FORWARDED_FOR'

# ============================================================

# ============================================================
# ============= CONTENT SECURITY POLICY (CSP) ================
# ============================================================
# Prevent XSS: batasi sumber resource yang boleh di-load browser

CSP_DEFAULT_SRC = ("'self'",)

# CSS: self + CDN yang dipakai (Bootstrap, Google Fonts, dll)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # needed untuk style inline di template (bisa diperketat nanti)
    "https://cdn.jsdelivr.net",
    "https://fonts.googleapis.com",
    "https://cdnjs.cloudflare.com",
)

# JavaScript: self + CDN
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # needed untuk script inline (onclick, dll)
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)

# Fonts
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "https://cdn.jsdelivr.net",
    "data:",
)

# Images: self + data URI + HTTPS apa saja (karena user bisa upload foto)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https:",
)

# Media (audio/video)
CSP_MEDIA_SRC = ("'self'",)

# Iframe: tidak boleh
CSP_FRAME_SRC = ("'none'",)

# Iframe ancestors (siapa yang boleh embed site ini)
CSP_FRAME_ANCESTORS = ("'none'",)

# AJAX/Fetch connections
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.anthropic.com",  # untuk chatbot SINTA
    "https://api.fonnte.com",     # untuk WhatsApp gateway
)

# Form action: cuma ke domain sendiri
CSP_FORM_ACTION = ("'self'",)

# Base URI: tidak boleh di-override via HTML
CSP_BASE_URI = ("'self'",)

# ============================================================
# =============== END CONTENT SECURITY POLICY ================
# ============================================================