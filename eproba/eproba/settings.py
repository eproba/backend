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

# When DEV is set to true, the app will show a dev label in the top right corner
DEV = os.environ.get("DEV", "") == "true"

# API version
API_VERSION = "0.4.0"  # Current API version of the app

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(" ")
ROOT_URLCONF = "eproba.urls"
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8000 http://localhost"
).split(" ")
SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://dev-eproba.zhr.pl",
    "https://eproba.zhr.pl",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
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
    "apps.wiki.apps.WikiConfig",
    "crispy_forms",
    "crispy_bulma",
    "fcm_django",
    "oauth2_provider",
    "constance",
    "maintenance_mode",
    "drf_spectacular",
    "dbbackup",
    "tinymce",
    "treebeard",
    "corsheaders",
    "django_cleanup.apps.CleanupConfig",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
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

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "oauth2_provider.backends.OAuth2Backend",
)

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    "SCOPES": {
        "openid": "OpenID Connect (twój identyfikator)",
        "profile": "Twój profil",
        "email": "Adres email",
        "teams": "Drużyny i zastępy",
        "worksheets": "Próby harcerskie",
        "wiki": "Artykuły wiki",
        "read": "Odczytywanie całej zawartości i danych na twoim koncie [wycofane]",
        "write": "Modyfikacja całej zawartoci i danych na twoim koncie [wycofane]",
    },
    "OIDC_ENABLED": True,
    "OAUTH2_VALIDATOR_CLASS": "apps.users.oauth_validators.CustomOAuth2Validator",
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https", "http", "com.czaplicki.eproba"],
    "REFRESH_TOKEN_GRACE_PERIOD_SECONDS": 120,
}

# Constance
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_CONFIG = {
    "ADS_WEB": (True, "Ads (web)"),
    "ADS_MOBILE": (True, "Ads (mobile)"),
    "WEB_MAINTENANCE_MODE": (False, "Web app maintenance [deprecated]"),
    "API_MAINTENANCE_MODE": (False, "API maintenance [deprecated]"),
    "MAINTENANCE_MODE": (False, "Maintenance mode"),
    "MINIMUM_APP_VERSION": (20240900, "Minimum app version"),
    "REQUIRE_EMAIL_VERIFICATION": (True, "Require email verification"),
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
                "constance.context_processors.config",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.google_auth_enabled",
                "apps.core.context_processors.dev_mode",
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
            "error_message": "To hasło zostało znalezione w bazie haseł, które zostały ujawnione w wyniku różnych ataków.",
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

# Media files (User uploaded content)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media")

# API Documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "Epoba API",
    "DESCRIPTION": "API for Eproba",
    "VERSION": API_VERSION,
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

# TinyMCE
TINYMCE_DEFAULT_CONFIG = {
    "promotion": False,
    "menubar": "file edit view insert format tools table help",
    "plugins": (
        "advlist autolink lists link image charmap preview anchor searchreplace emoticons "
        "visualblocks code fullscreen insertdatetime media table code help wordcount"
    ),
    "toolbar": (
        "undo redo | "
        "bold italic underline strikethrough | "
        "blocks fontfamily fontsize | "
        "alignleft aligncenter alignright alignjustify | "
        "forecolor backcolor removeformat | "
        "numlist bullist checklist | "
        "outdent indent hr | "
        "charmap emoticons | "
        "fullscreen preview save | "
        "insertfile image media pageembed template link anchor codesample | "
        "code"
    ),
}

# Logging configuration
# Custom logging to ensure console output works regardless of DEBUG setting
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            # Remove the require_debug_true filter to allow console logging even when DEBUG is False
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        # Add application-specific loggers
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Root logger for any other messages
        "": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}
