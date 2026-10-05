"""
Production settings — DEBUG off, security headers, require HTTPS.
Use: DJANGO_ENV=production or DJANGO_SETTINGS_MODULE=config.settings.production
Ensure: SECRET_KEY, ALLOWED_HOSTS, DB_* and CORS are set in .env.
"""
from decouple import config
from .base import *  # noqa: F401, F403

SECRET_KEY = config('SECRET_KEY')  # Required in prod; no default
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
if config('USE_HTTPS', default=False, cast=bool):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Production: JSON only (no BrowsableAPIRenderer)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# Structured JSON logging for log aggregation
LOGGING['formatters']['json'] = {'()': 'config.logging.JsonFormatter'}
for _handler in LOGGING['handlers'].values():
    _handler['formatter'] = 'json'
