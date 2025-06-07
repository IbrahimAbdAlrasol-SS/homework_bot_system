from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database for development
DATABASES['default'].update({
    'NAME': 'homework_bot_dev',
})

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Disable security features for development
SECURE_SSL_REDIRECT = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'ALLOWALL'

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging for development
LOGGING['handlers']['file']['filename'] = BASE_DIR / 'logs' / 'development.log'
LOGGING['root']['level'] = 'DEBUG'