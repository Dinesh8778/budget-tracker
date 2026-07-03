import os
from pathlib import Path
import environ
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'django-insecure-default-secret-key-for-development'),
    ALLOWED_HOSTS=(list, ['*']),
)

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')


INSTALLED_APPS = [
    'jazzmin',  # if you're using jazzmin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp.apps.MyappConfig',  # Use the app config class
     # ... existing apps
    'django_crontab',
]

AUTH_USER_MODEL = 'myapp.User'
CRONJOBS = [
    ('0 0 * * *', 'myapp.management.commands.process_emi_payments.Command.handle', '>> /tmp/emi_cron.log')
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # your_project/settings.py


    # ... existing middleware
    'myapp.middleware.EMIPaymentMiddleware',
]

ROOT_URLCONF = 'your_project.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Make sure this points to your templates directory
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
WSGI_APPLICATION = 'your_project.wsgi.application'

db_url = os.environ.get('DATABASE_URL', '')
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False if not db_url or 'sqlite' in db_url else True
    )
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# Ensure the local static directory exists to avoid Django startup warnings
LOCAL_STATIC_DIR = BASE_DIR / 'static'
if not LOCAL_STATIC_DIR.exists():
    os.makedirs(LOCAL_STATIC_DIR, exist_ok=True)

STATICFILES_DIRS = [LOCAL_STATIC_DIR]
STATIC_ROOT = BASE_DIR / 'staticfiles'

if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Add these to your settings.py
# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Admin settings
ADMIN_SITE_HEADER = "MyApp Administration"
ADMIN_SITE_TITLE = "MyApp Admin Portal"
ADMIN_INDEX_TITLE = "Welcome to MyApp Admin"
# Jazzmin Settings
JAZZMIN_SETTINGS = {
    "site_title": "MyApp Admin",
    "site_header": "MyApp Administration",
    "site_brand": "MyApp",
    "welcome_sign": "Welcome to MyApp Admin",
    "copyright": "MyApp Ltd",
    "search_model": "myapp.User",
}