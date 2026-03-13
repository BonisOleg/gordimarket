"""
Налаштування для продакшну (Render)
"""
from .base import *
import dj_database_url
import os

DEBUG = False

# Додаємо PostgreSQL specific apps для Full-Text Search
INSTALLED_APPS = INSTALLED_APPS + ['django.contrib.postgres']

# Override SECRET_KEY for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# ALLOWED_HOSTS для Render
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# CSRF trusted origins для Render
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://localhost').split(',')

# Database для продакшну
if os.getenv('DATABASE_URL'):
    # Production database (PostgreSQL on Render)
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Development database (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Static and Media files для продакшну
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cloudinary configuration для зберігання media файлів
import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'demo'),
    api_key=os.getenv('CLOUDINARY_API_KEY', ''),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', ''),
    secure=True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', 'demo'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}

MEDIA_URL = '/media/'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Whitenoise також обслуговує media файли на production
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 31536000  # 1 рік кешування для статичних файлів

# Додаємо Whitenoise middleware після SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Security settings для продакшну
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Дозволяємо JavaScript читати CSRF token
# ✅ iOS Safari ITP fix: SameSite=None дозволяє cookies на iOS при HTTPS
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE = 'None'
X_FRAME_OPTIONS = 'DENY'

# Email settings для продакшну
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
# Використовуємо той самий email що і EMAIL_HOST_USER для FROM_EMAIL
DEFAULT_FROM_EMAIL = f"Shop <{os.getenv('EMAIL_HOST_USER', 'noreply@example.com')}>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Додаткові налаштування для Gmail
EMAIL_TIMEOUT = 30  # 30 секунд таймаут

# Виводимо налаштування email для діагностики (без паролю!)
import logging
email_logger = logging.getLogger('django.core.mail')
email_logger.info(f"📧 Email settings loaded:")
email_logger.info(f"   EMAIL_HOST: {EMAIL_HOST}")
email_logger.info(f"   EMAIL_PORT: {EMAIL_PORT}")
email_logger.info(f"   EMAIL_USE_TLS: {EMAIL_USE_TLS}")
email_logger.info(f"   EMAIL_HOST_USER: {EMAIL_HOST_USER}")
email_logger.info(f"   DEFAULT_FROM_EMAIL: {DEFAULT_FROM_EMAIL}")
email_logger.info(f"   EMAIL_HOST_PASSWORD: {'SET' if EMAIL_HOST_PASSWORD else 'NOT SET'}")

# Логування для продакшну - з детальною діагностикою
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # ДЕТАЛЬНЕ ЛОГУВАННЯ EMAIL
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.users': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Кешування - використовуємо Redis якщо доступний, інакше locmem
REDIS_URL = os.getenv('REDIS_URL', None)

if REDIS_URL:
    # Використовуємо Redis для кешування (рекомендовано для production)
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'RETRY_ON_TIMEOUT': True,
                'MAX_CONNECTIONS': 50,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                # Hiredis is optional - use if available for better performance
                # 'PARSER_CLASS': 'redis.connection.HiredisParser',
            },
            'KEY_PREFIX': 'intshop',
            'TIMEOUT': 300,  # 5 хвилин за замовчуванням
        }
    }
    
    # Використовуємо Redis для сесій (опціонально)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
    
    import logging
    cache_logger = logging.getLogger('django.core.cache')
    cache_logger.info(f"✅ Redis cache enabled: {REDIS_URL}")
else:
    # Fallback на локальну пам'ять
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,
        }
    }
    
    import logging
    cache_logger = logging.getLogger('django.core.cache')
    cache_logger.info("⚠️  Redis not configured, using locmem cache (not recommended for production)")

# Додаткові налаштування для Render
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Вимкнути перевірку ALLOWED_HOSTS для healthcheck
ALLOWED_HOSTS.append('.onrender.com')

# Налаштування для Django 4.2+ 
USE_TZ = True
TIME_ZONE = 'Europe/Kiev'

# Налаштування завершено - STORAGES вже налаштований вище

# Секрет для cron тригера (додати в Render Environment Variables)
CRON_SECRET = os.getenv('CRON_SECRET', 'change-me-in-production')

# Збільшити timeout для довгих операцій імпорту
CONN_MAX_AGE = 600  # 10 хвилин
