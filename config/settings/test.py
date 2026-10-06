"""
Test settings for ELECTROCART.
Configured for deterministic, fast test execution with SQLite and in-memory email.
"""

from pathlib import Path
from .base import *

DEBUG = False
ALLOWED_HOSTS = ["*"]

# Fast password hasher for test speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email backend for testing confirmation and notification flows
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# File-based test database supporting concurrency tests per Standing Orders Section 6
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
        "TEST": {
            "NAME": BASE_DIR / "test_db.sqlite3",
        },
    }
}

# In-memory cache for session and rate-limit testing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "electrocart-test-cache",
    }
}

# Vite dev mode disabled for tests
DJANGO_VITE["default"]["dev_mode"] = False

# Razorpay deterministic test credentials
RAZORPAY_KEY_ID = "rzp_test_mock_key_id"
RAZORPAY_KEY_SECRET = "rzp_test_mock_secret_key"
RAZORPAY_WEBHOOK_SECRET = "rzp_test_mock_webhook_secret"

# Plain staticfiles storage for tests (no manifest compilation required)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
