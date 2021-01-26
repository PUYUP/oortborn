from .base import *
from .project import *

import sentry_sdk

from sentry_sdk.integrations.django import DjangoIntegration
from corsheaders.defaults import default_headers

DEBUG = False
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    '[::1]', 
    '192.168.1.115',
    'api.daftarbelanja.com',
    'app.daftarbelanja.com',
]


# SENTRY
sentry_sdk.init(
    dsn="https://03b90e71d21646688b3c26fc13c9de50@o400235.ingest.sentry.io/5570476",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)


# Django Sessions
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/settings/
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = False

SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 5
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'


# Django csrf
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/csrf/
CSRF_COOKIE_DOMAIN = '.daftarbelanja.com'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
    'daftar-belanja-001.firebaseapp.com',
    '.daftarbelanja.com'
]


# Django CORS
# ------------------------------------------------------------------------------
# https://pypi.org/project/django-cors-headers/
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost',
    'http://localhost:8100',
    'https://app.daftarbelanja.com',
    'https://daftar-belanja-001.firebaseapp.com',
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'ngsw-bypass',
]


# Static files (CSS, JavaScript, Images)
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'daftarbelanja_db',
        'USER': 'daftarbelanja_db_user',
        'PASSWORD': '6+Zwx37G3)EhSx',
        'HOST': HOST,   # Or an IP Address that your DB is hosted on
        'PORT': '',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        }
    }
}


# CHANNELS
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["redis://127.0.0.1:6379"],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    },
}


# CACHING SERVER
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        },
        'KEY_PREFIX': 'oort_cache'
    }
}


# GMAIL SMTP
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'hellopuyup@gmail.com'
EMAIL_HOST_PASSWORD = 'ind0nesi@' #past the key or password app here
EMAIL_PORT = 587
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
