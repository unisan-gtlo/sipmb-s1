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
   
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
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
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
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

# =============================================================
# LOGGING
# =============================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'sipmb.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'