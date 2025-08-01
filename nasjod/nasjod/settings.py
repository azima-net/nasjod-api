"""
Django settings for nasjod project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from datetime import timedelta

import sentry_sdk


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost,http://127.0.0.1').split(',')

# Ensure you have this setting if you're behind a proxy like Nginx
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Get ALLOWED_HOSTS from environment variables
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    'storages',
    'corsheaders',
    "rest_framework",
    "drf_spectacular",
    "django.contrib.gis",
    "core",
    "authentification",
    "user",
    "masjid",
    "prayertime",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS_ENV = os.getenv('CORS_ALLOW_ALL_ORIGINS_ENV', 'False') == 'True'
if CORS_ALLOW_ALL_ORIGINS_ENV:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

ROOT_URLCONF = "nasjod.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates'),],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nasjod.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASS"),
        'HOST': os.environ.get("DB_HOST"),
        'PORT': '',
    }
}

MAX_RETRIES_DB = 10

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'throttling.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django_throttling': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_ROOT = '/vol/web/static'
STATIC_URL = '/static/'


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# USER
AUTH_USER_MODEL = "user.User"

S3_STORAGE_BACKEND = bool(int(os.environ.get("S3_STORAGE_BACKEND", 1)))
if S3_STORAGE_BACKEND is True:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_URL_PROTOCOL = "https"
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_USE_SSL = True
    AWS_S3_VERIFY_SSL = True
    AWS_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
    AWS_S3_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("R2_STORAGE_BUCKET_NAME")
    AWS_DEFAULT_ACL = None
    # AWS_S3_REGION_NAME = os.environ.get("S3_STORAGE_BUCKET_REGION", "us-east-1")
    # AWS_QUERYSTRING_AUTH = False

# If throttling is disabled, set an empty tuple for throttle classes
DEFAULT_THROTTLE_CLASSES = ()
DEFAULT_THROTTLE_RATES = {}



# Fetch the value from the environment variable, default is False (disabled)
THROTTLE_ENABLED = os.getenv('THROTTLE_ENABLED', 'False') == 'True'
if THROTTLE_ENABLED:
    # If throttling is enabled, set the throttle classes and rates
    DEFAULT_THROTTLE_CLASSES = (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    )
    DEFAULT_THROTTLE_RATES = {
        'user': '10000/day',
        'anon': '1000/day',
        'anon_create_masjid': '5/min',
    }

REST_FRAMEWORK = {
    #SCHEMA_OPENAPI
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Authentication settings
    #  'DEFAULT_AUTHENTICATION_CLASSES': (
    #     'rest_framework_simplejwt.authentication.JWTAuthentication',
    # ),

    # Permission settings
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     'rest_framework.permissions.IsAuthenticated',
    # ),

    # Pagination settings
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Filter
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),

    # Throttling settings
    'DEFAULT_THROTTLE_CLASSES': DEFAULT_THROTTLE_CLASSES,
    'DEFAULT_THROTTLE_RATES': DEFAULT_THROTTLE_RATES,

    # Renderer settings
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),

    # Parser settings
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),

    # Exception handling
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    # Content negotiation
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'rest_framework.negotiation.DefaultContentNegotiation',

    # API versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Validation age
VALIDATE_AGE = False
MINIMUM_AGE_LIMIT = 10

MASJID_LOOKUP_FIELD = "masjid_uuid"

SPECTACULAR_SETTINGS = {
    'TITLE': 'Nasjod API',
    'DESCRIPTION': 'API documentation for the Nasjod project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # 'SECURITY': [
    #     {
    #         'BearerAuth': []
    #     }
    # ],
    # 'COMPONENT_SPLIT_REQUEST': True,
    # 'SECURITY_DEFINITIONS': {
    #     'BearerAuth': {
    #         'type': 'http',
    #         'scheme': 'bearer',
    #         'bearerFormat': 'JWT',
    #     }
    # },
}


sentry_sdk.init(
    dsn=os.getenv('SENTRY_DNS'),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)

# Security settings
# https://docs.djangoproject.com/en/5.0/topics/security/
if DEBUG:
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    SECURE_HSTS_SECONDS = 31536000  # 1 year in production
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
