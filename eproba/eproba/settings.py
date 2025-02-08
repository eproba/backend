import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app

LOGGER = logging.getLogger(__name__)

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "xp^6=5g0y=^mwy$+jx7^bf!5s&zr$slvz=0lvy4)n55i#0+ib2"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "") == "true"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(" ")
ROOT_URLCONF = "eproba.urls"
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8000 http://localhost"
).split(" ")
SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
WSGI_APPLICATION = "eproba.wsgi.application"

CRISPY_ALLOWED_TEMPLATE_PACKS = ("bulma",)

CRISPY_TEMPLATE_PACK = "bulma"

# Firebase
try:
    FIREBASE_APP = initialize_app(
        credentials.Certificate("secrets/firebase-admin-sdk.json")
    )
except FileNotFoundError:
    LOGGER.warning("Firebase credentials file not found. Notifications are disabled.")
    FIREBASE_APP = None
FCM_DJANGO_SETTINGS = {"APP_VERBOSE_NAME": "Powiadomienia (FCM)"}

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "rest_framework",
    "apps.blog.apps.BlogConfig",
    "apps.core.apps.CoreConfig",
    "apps.worksheets.apps.WorksheetConfig",
    "apps.users.apps.UsersConfig",
    "apps.teams.apps.TeamsConfig",
    "crispy_forms",
    "crispy_bulma",
    "fcm_django",
    "oauth2_provider",
    "constance",
    "maintenance_mode",
    "drf_spectacular",
    "dbbackup",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
    "apps.core.middleware.APIMaintenanceMiddleware",
]

# API
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Accounts and authentication
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "worksheets:worksheets"
LOGOUT_REDIRECT_URL = "frontpage"
AUTH_USER_MODEL = "users.User"

GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
if not GOOGLE_OAUTH_CLIENT_ID:
    LOGGER.warning("GOOGLE_OAUTH_CLIENT_ID not set, Google login is disabled.")

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    "SCOPES": {
        "read": "Odczytywanie zawartości i danych na twoim koncie",
        "write": "Modyfikacja zawartoci i danych na twoim koncie",
    },
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https", "com.czaplicki.eproba"],
}

# Constance
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_CONFIG = {
    "ADS_WEB": (True, "Ads (web)"),
    "ADS_MOBILE": (True, "Ads (mobile)"),
    "WEB_MAINTENANCE_MODE": (False, "Web app maintenance"),
    "API_MAINTENANCE_MODE": (False, "API maintenance"),
    "MINIMUM_APP_VERSION": (20240900, "Minimum app version"),
}

# Maintenance mode
MAINTENANCE_MODE_TEMPLATE = "errors/503.html"
MAINTENANCE_MODE_IGNORE_ADMIN_SITE = True
# MAINTENANCE_MODE_IGNORE_SUPERUSER = True
MAINTENANCE_MODE_IGNORE_URLS = (
    r"^/api/",
    r"^/robots.txt",
    r"^/app-ads.txt",
    r"^/ads.txt",
    r"^/sitemap.xml",
    r"^/contact",
    r"^/privacy-policy",
    r"^/gdpr",
    r"^/terms-of-service",
    r"^/site-management",
    r"^/login",
    r"^/static/images/icons/favicon.svg",
)

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.google_auth_enabled",
            ],
        },
    },
]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
if os.environ.get("DATABASE", "sqlite") == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif os.environ.get("DATABASE", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DATABASE_NAME"),
            "USER": os.environ.get("DATABASE_USER"),
            "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
            "HOST": os.environ.get("DATABASE_HOST"),
            "PORT": os.environ.get("DATABASE_PORT"),
        }
    }
else:
    raise ValueError("Invalid database type.")

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
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
    {
        "NAME": "pwned_passwords_django.validators.PwnedPasswordsValidator",
        "OPTIONS": {
            "error_message": "To hasło zostało znalezione w bazie haseł, które zostały ujawnione w wyniku różnych ataków. Wybierz inne hasło. Aby dowiedzieć się więcej, odwiedź https://haveibeenpwned.com",
            "help_message": "Twoje hasło nie może być używane w zbyt wielu miejscach.",
        },
    },
]

# Emails
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = "Epróba <eproba@zhr.pl>"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = "pl"

TIME_ZONE = "CET"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")

# API Documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "Epoba API",
    "DESCRIPTION": "API for Eproba",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api",
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
}

# Database backup
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {
    "location": os.environ.get("DBBACKUP_STORAGE_LOCATION", BASE_DIR / "backups"),
}
