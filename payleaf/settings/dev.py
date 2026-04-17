from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = ['*']

# Local development — relax security cookies
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use LocMemCache for local dev without Redis.
# Docker-compose overrides this via REDIS_URL env var.
REDIS_URL = os.environ.get('REDIS_URL', '')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
else:
    # Fallback to DB sessions when no Redis
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
