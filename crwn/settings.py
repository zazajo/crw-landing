"""
Django settings for crwn project - Development Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-this-in-production')
DEBUG = True  # Changed to True for development

# Site configuration
SITE_URL = 'http://localhost:8000'  # Changed to HTTP for development
SITE_NAME = 'CrownieVerse'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'crownie',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crownie.middleware.DiscordConnectionRequiredMiddleware',
]

ROOT_URLCONF = 'crwn.urls'

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
                'crwn.context_processor.site_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'crwn.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication
AUTH_USER_MODEL = 'crownie.User'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ===== DEVELOPMENT SETTINGS =====
# Allow all hosts for local development
ALLOWED_HOSTS = ['*']

# Disable SSL for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = None  # Disable for development

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
]

# CORS for development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
]
CORS_ALLOW_ALL_ORIGINS = True  # Enable for development
CORS_ALLOW_CREDENTIALS = True

# Discord OAuth for development
DISCORD_REDIRECT_URI = 'http://localhost:8000/discord/callback/'  # HTTP for dev
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID')
DISCORD_OAUTH_SCOPES = 'identify guilds.join'

# Django Sites Framework
SITE_ID = 1

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API for dev
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# Email (using console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',  # Simple cache for dev
    }
}

# Logging for development
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
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
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
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'crownie': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# File upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# ===== UTILITY FUNCTION =====
def is_development():
    """Check if we're in development mode."""
    return DEBUG is True

def is_production():
    """Check if we're in production mode."""
    return DEBUG is False and 'crownieverse.xyz' in SITE_URL

# ===== DEVELOPMENT-SPECIFIC SETTINGS =====
if is_development():
    print("🔧 Running in DEVELOPMENT mode")
    
    # Additional development apps
    INSTALLED_APPS += [
        'django_extensions',  # Useful for development
    ]
    
    # Development middleware
    MIDDLEWARE += [
        
    ]
    
    # Debug toolbar
    INSTALLED_APPS += []
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    
    # Django Extensions
    SHELL_PLUS = "ipython"
    
    # Disable HTTPS requirements completely
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    
    # Allow iframes in development
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    
    # Disable security headers for easier development
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False

# ===== PRODUCTION SETTINGS (commented out for now) =====
# Uncomment these when deploying to production:
"""
if is_production():
    print("🚀 Running in PRODUCTION mode")
    
    # Production security settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Production hosts
    ALLOWED_HOSTS = [
        'www.crownieverse.xyz',
        'crownieverse.xyz',
        'crownie.pythonanywhere.com',
    ]
    
    CSRF_TRUSTED_ORIGINS = [
        'https://www.crownieverse.xyz',
        'https://crownieverse.xyz',
        'https://crownie.pythonanywhere.com',
    ]
    
    # Production CORS
    CORS_ALLOWED_ORIGINS = [
        'https://www.crownieverse.xyz',
        'https://crownieverse.xyz',
    ]
    CORS_ALLOW_ALL_ORIGINS = False
    
    # Production Discord OAuth
    DISCORD_REDIRECT_URI = 'https://www.crownieverse.xyz/discord/callback/'
    
    # Production cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'crownie-production',
        }
    }
    
    # Production logging
    LOGGING['handlers']['file']['level'] = 'ERROR'
    LOGGING['loggers']['django.request']['level'] = 'ERROR'
    LOGGING['loggers']['crownie']['level'] = 'INFO'
    
    # Production email (configure your SMTP settings)
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_HOST = 'smtp.gmail.com'
    # EMAIL_PORT = 587
    # EMAIL_USE_TLS = True
    # EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    # EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
"""