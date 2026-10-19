"""
Base Django settings for ELECTROCART.

Production-grade commerce configuration targeting Python 3.13 and Django 5.2 LTS.
Specific environment overrides are loaded via config.settings.local or
config.settings.production.
"""

from decimal import Decimal
import os
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# ==============================================================================
# CORE SECURITY & APPLICATION IDENTITY
# ==============================================================================

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required in .env.")

# DEBUG is explicitly False in base; enabled in local.py
DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in csrf_origins.split(",") if origin.strip()
]

SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "django_vite",
    "csp",
]

# Local apps:
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.tax",
    "apps.shipping",
    "apps.catalog",
    "apps.inventory",
    "apps.cart",
    "apps.wishlist",
    "apps.promotions",
    "apps.orders",
    "apps.payments",
    "apps.search",
]

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "apps.core.middleware.SensitivePageHeadersMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.core.middleware.MotionDebugMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # Required by allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.storefront_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL environment variable is required. Configure local PostgreSQL credentials in .env."
    )

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# AUTHENTICATION & ALLAUTH (Targeting allauth 65.x)
# ==============================================================================

# Custom user model will be enabled in File 7 (apps/accounts):
# AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Modern allauth 65.x configuration
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Electrocart] "
ACCOUNT_ADAPTER = "apps.accounts.adapter.CustomAccountAdapter"

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================================================================
# INTERNATIONALIZATION & CURRENCY
# ==============================================================================

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC & MEDIA ASSETS
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# NOTE: config.settings.test will override STORAGES['staticfiles'] with plain
# django.contrib.staticfiles.storage.StaticFilesStorage to prevent test execution
# failures when manifest static assets have not been compiled.

def whitenoise_immutable_file_test(path, url):
    """
    Identifies versioned assets that can be cached forever:
    Vite bundles under /dist/ and Django CompressedManifestStaticFilesStorage hashed files.
    """
    import re
    return "/dist/" in url or bool(re.search(r"([.-][0-9a-fA-F]{8,32}\.)", url))

WHITENOISE_IMMUTABLE_FILE_TEST = whitenoise_immutable_file_test
WHITENOISE_MAX_AGE = 31536000  # 1 year for immutable hashed assets

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================================================================
# EMAIL INFRASTRUCTURE (WP3.2)
# Controlled by EMAIL_MODE: 'file' (default for grading), 'console', or 'smtp'.
# ==============================================================================

EMAIL_MODE = os.environ.get("EMAIL_MODE", "file").strip().lower()
EMAIL_FILE_PATH = BASE_DIR / ".emails"
DEMO_EMAIL_FALLBACK = os.environ.get("DEMO_EMAIL_FALLBACK", "0").strip() in ("1", "true", "True")

if EMAIL_MODE == "console":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
elif EMAIL_MODE == "smtp":
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com").strip()
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "").strip()
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").strip()
    if DEMO_EMAIL_FALLBACK:
        EMAIL_BACKEND = "apps.core.email_backends.FallbackSmtpFileEmailBackend"
    else:
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    # Default 'file' mode for faculty grading and offline inspection
    EMAIL_BACKEND = "apps.core.email_backends.InspectableFileEmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Electrocart <noreply@electrocart.local>"
)


# ==============================================================================
# COOKIE & SESSION SECURITY
# ==============================================================================

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# ==============================================================================
# CONTENT SECURITY POLICY (django-csp 4.x dictionary style)
# ==============================================================================

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "https://checkout.razorpay.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",  # Design tokens inline fallback
        ],
        "img-src": [
            "'self'",
            "data:",
            "blob:",  # Three.js canvas texture creation
            "https://m.media-amazon.com",  # Dataset marketplace photos
        ],
        "media-src": [
            "'self'",
            "blob:",
        ],
        "frame-src": [
            "'self'",
            "https://api.razorpay.com",
        ],
        "frame-ancestors": ["'none'"],
        "connect-src": [
            "'self'",
            "https://lumberjack.razorpay.com",
            "https://m.media-amazon.com",
        ],
        "font-src": ["'self'"],
        "object-src": ["'none'"],
        "base-uri": ["'self'"],
    }
}

MOTION_DEBUG = False

# NOTE: config.settings.local will extend script-src and connect-src to include
# the Vite development server (http://localhost:5173).

# ==============================================================================
# FRONTEND BUILD INTEGRATION (django-vite)
# ==============================================================================

DJANGO_VITE = {
    "default": {
        "dev_mode": False,
        "manifest_path": BASE_DIR / "static" / "dist" / ".vite" / "manifest.json",
        "static_url_prefix": "dist/",
    }
}

# ==============================================================================
# COMMERCE SEED DEFAULTS (Apps.shipping.models.ShippingConfig model defaults)
# ==============================================================================

# The ShippingConfig singleton model is the runtime source of truth.
# These values are strictly SEED DEFAULTS for migrations and seeding scripts.
# Runtime commerce code must NEVER read these settings constants directly.
DEFAULT_FREE_SHIPPING_THRESHOLD = Decimal("499.00")
DEFAULT_STANDARD_SHIPPING_FEE = Decimal("40.00")  # Flagged in admin
DEFAULT_COD_FEE = Decimal("0.00")

# ==============================================================================
# PAYMENT PROVIDERS: RAZORPAY
# ==============================================================================

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

# ==============================================================================
# INDIAN GST & SELLER COMPLIANCE
# ==============================================================================

# SELLER_STATE has NO default. Production settings raise ImproperlyConfigured if omitted.
# In local development, an empty value warns on startup and tax calculations raise errors.
SELLER_STATE = os.environ.get("SELLER_STATE", "").strip()
SELLER_GSTIN = os.environ.get("SELLER_GSTIN", "").strip()
SELLER_LEGAL_NAME = os.environ.get("SELLER_LEGAL_NAME", "").strip()
SELLER_ADDRESS = os.environ.get("SELLER_ADDRESS", "").strip()

CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"
CART_MAX_QTY_PER_LINE = 10

# ==============================================================================
# LOGGING INFRASTRUCTURE & SECURITY REDACTION
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "sensitive_redaction": {
            "()": "apps.core.logging_filters.SensitiveDataFilter",
        },
    },
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["sensitive_redaction"],
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Media slot placeholder labels (True in local, False in production)
SHOW_PLACEHOLDER_LABELS = False

# Guest COD OTP Verification Gate (Phase R8)
GUEST_COD_OTP_REQUIRED = os.environ.get("GUEST_COD_OTP_REQUIRED", "1").lower() in ("1", "true", "yes")


