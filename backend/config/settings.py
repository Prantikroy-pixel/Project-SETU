"""
Django settings for SETU backend project.
"""

from pathlib import Path
import os
import sys
from datetime import timedelta
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Include root repository directory in sys.path to allow direct matching_engine import
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

from django.core.exceptions import ImproperlyConfigured

# Quick-start development settings - unsuitable for production
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-setu-development-secret-key-do-not-use-in-production'
    else:
        raise ImproperlyConfigured("CRITICAL SECURITY VIOLATION: SECRET_KEY environment variable must be set in production.")

allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
else:
    # Strict fallback for local development (no wildcard)
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']
    if os.getenv('VERCEL') == '1' or 'VERCEL' in os.environ:
        ALLOWED_HOSTS.append('*')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party packages
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # SETU apps
    'accounts',
    'core',
    'logistics',
    'matching',
    'dashboard',
]

# Check if GeoDjango GIS app is usable in this environment
try:
    from django.contrib.gis.gdal import HAS_GDAL
    if HAS_GDAL:
        INSTALLED_APPS.insert(0, 'django.contrib.gis')
except Exception:
    pass

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database configuration with transparent SQLite fallback
DATABASE_URL = os.getenv('DATABASE_URL')
USE_SQLITE = os.getenv('USE_SQLITE', 'False').lower() in ('true', '1')

IS_VERCEL = os.getenv('VERCEL') == '1' or 'VERCEL' in os.environ
if IS_VERCEL:
    SQLITE_DB_PATH = Path('/tmp') / 'db.sqlite3'
    # Copy pre-populated SQLite DB to /tmp to preserve migrations and seed data
    original_db = BASE_DIR / 'db.sqlite3'
    if original_db.exists() and not SQLITE_DB_PATH.exists():
        try:
            import shutil
            shutil.copy2(original_db, SQLITE_DB_PATH)
        except Exception:
            pass
else:
    SQLITE_DB_PATH = BASE_DIR / 'db.sqlite3'

def _is_postgres_available(host, port, user, password, dbname):
    if USE_SQLITE:
        return False
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=1
        )
        conn.close()
        return True
    except Exception:
        return False

if DATABASE_URL and not USE_SQLITE:
    import urllib.parse
    parsed_url = urllib.parse.urlparse(DATABASE_URL)
    pg_host = parsed_url.hostname or 'localhost'
    pg_port = parsed_url.port or 5432
    pg_user = parsed_url.username or 'postgres'
    pg_pass = parsed_url.password or ''
    pg_name = parsed_url.path.lstrip('/')

    if _is_postgres_available(pg_host, pg_port, pg_user, pg_pass, pg_name):
        engine = 'django.db.backends.postgresql'
        if 'postgis' in parsed_url.scheme:
            try:
                from django.contrib.gis.db.backends.postgis import base
                engine = 'django.contrib.gis.db.backends.postgis'
            except Exception:
                engine = 'django.db.backends.postgresql'

        DATABASES = {
            'default': {
                'ENGINE': engine,
                'NAME': pg_name,
                'USER': pg_user,
                'PASSWORD': pg_pass,
                'HOST': pg_host,
                'PORT': pg_port,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': SQLITE_DB_PATH,
            }
        }
elif os.getenv('DB_NAME') and not USE_SQLITE:
    pg_host = os.getenv('DB_HOST', 'localhost')
    pg_port = os.getenv('DB_PORT', '5432')
    pg_user = os.getenv('DB_USER', 'postgres')
    pg_pass = os.getenv('DB_PASSWORD', '')
    pg_name = os.getenv('DB_NAME')

    if _is_postgres_available(pg_host, pg_port, pg_user, pg_pass, pg_name):
        db_engine = 'django.db.backends.postgresql'
        try:
            from django.contrib.gis.db.backends.postgis import base
            db_engine = 'django.contrib.gis.db.backends.postgis'
        except Exception:
            db_engine = 'django.db.backends.postgresql'

        DATABASES = {
            'default': {
                'ENGINE': os.getenv('DB_ENGINE', db_engine),
                'NAME': pg_name,
                'USER': pg_user,
                'PASSWORD': pg_pass,
                'HOST': pg_host,
                'PORT': pg_port,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': SQLITE_DB_PATH,
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': SQLITE_DB_PATH,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', str(BASE_DIR / 'media'))

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# SimpleJWT configuration
jwt_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MIN', '60'))
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=jwt_lifetime),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration (Strict Origin Whitelisting in production, open in debug)
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# Whitelist Vite dev frontends and local dev ports
_DEFAULT_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:5174',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:5174',
]

cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS')
if cors_origins_env:
    CORS_ALLOWED_ORIGINS = list(set(
        [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
        + _DEFAULT_ALLOWED_ORIGINS
    ))
else:
    CORS_ALLOWED_ORIGINS = _DEFAULT_ALLOWED_ORIGINS

# Automatically permit all Vercel production and preview deployment domains
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

# ─────────────────────────────────────────────────────────────────────────────
# HTTP Security Response Headers (SEC-009)
# ─────────────────────────────────────────────────────────────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Production HTTPS and Transport Security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 Year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Weather & SMS Gateways API Keys
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
SMS_GATEWAY_API_KEY = os.getenv('SMS_GATEWAY_API_KEY', '')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'