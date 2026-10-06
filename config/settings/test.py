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
