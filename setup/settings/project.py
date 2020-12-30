from datetime import timedelta
from django.contrib.messages import constants as messages
from firebase_admin import credentials, initialize_app
import firebase_admin

from .base import *


# GLOBAL CONFIGURATIONS
APP_NAME = 'Daftar Belanja'
PROJECT_URL = 'www.daftarbelanja.com'
PAGINATION_PER_PAGE = 15
LOGIN_WITH_JWT = True
RECOVERY_PASSWORD_CHECK_ACCOUNT = True # If true in recovery password need make sure account exist


# REGISTRATION REQUIREMENTS
STRICT_EMAIL = False
STRICT_EMAIL_VERIFIED = False
STRICT_EMAIL_DUPLICATE = False

STRICT_MSISDN = False
STRICT_MSISDN_VERIFIED = False
STRICT_MSISDN_DUPLICATE = False

LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/person/login/'


# Application definition
PROJECT_APPS = [
    'channels',
    'corsheaders',
    'rest_framework',
    'apps.person.apps.PersonConfig',
    'apps.shopping.apps.ShoppingConfig',
]
INSTALLED_APPS = INSTALLED_APPS + PROJECT_APPS


# MIDDLEWARES
PROJECT_MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
]
MIDDLEWARE = PROJECT_MIDDLEWARE + MIDDLEWARE


# Specifying authentication backends
# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/
AUTHENTICATION_BACKENDS = ['apps.person.utils.auth.LoginBackend',]


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
AUTH_USER_MODEL = 'person.User'


# CACHING
# https://docs.djangoproject.com/en/2.2/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '10.0.2.2:11211',
        'OPTIONS': {
            'server_max_value_length': 1024 * 1024 * 2,
        },
        'KEY_PREFIX': 'oort_cache'
    }
}


# MESSAGES
# https://docs.djangoproject.com/en/3.0/ref/contrib/messages/
MESSAGE_TAGS = {
    messages.DEBUG: 'alert alert-dark shadow-sm',
    messages.INFO: 'alert alert-info shadow-sm',
    messages.SUCCESS: 'alert alert-info success shadow-sm',
    messages.WARNING: 'alert alert-warning shadow-sm',
    messages.ERROR: 'alert alert-error shadow-sm',
}


# Django Sessions
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/settings/
SESSION_SAVE_EVERY_REQUEST = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# Static files (CSS, JavaScript, Images)
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/howto/static-files/
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media/')


# Django Simple JWT
# ------------------------------------------------------------------------------
# https://github.com/davesque/django-rest-framework-simplejwt
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
}


# Django Rest Framework (DRF)
# ------------------------------------------------------------------------------
# https://www.django-rest-framework.org/
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': PAGINATION_PER_PAGE
}


# Email Configuration
# https://docs.djangoproject.com/en/3.0/topics/email/
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


# REDIS
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
REDIS_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT


# Firebase configuration
FIREBASE_CRED_FILE = '%s/%s' % (PROJECT_PATH, 'firebase-cred.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = FIREBASE_CRED_FILE
default_app = firebase_admin.initialize_app()


# SENDGRID
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = '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'
EMAIL_PORT = 587
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
