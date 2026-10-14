"""
Local development settings for ELECTROCART.
"""

import warnings
from .base import *

DEBUG = True

# Allow testserver and localhost for testing
ALLOWED_HOSTS = list(ALLOWED_HOSTS) + ["testserver"]
CSRF_TRUSTED_ORIGINS = list(CSRF_TRUSTED_ORIGINS) + [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Development motion debugging: allows ?motion=1|2|3 to force motion tiers
MOTION_DEBUG = True

# Display small "Placeholder" badge on media slots in local dev
SHOW_PLACEHOLDER_LABELS = True

# Warn loudly on local startup if SELLER_STATE is missing
if not SELLER_STATE:
    warnings.warn(
        "SELLER_STATE is empty in .env. Tax calculations will raise an ImproperlyConfigured error when invoked.",
        UserWarning,
        stacklevel=2,
    )

# Warn if SECRET_KEY is using the placeholder template
if SECRET_KEY.startswith("CHANGE_ME"):
    warnings.warn(
        "SECRET_KEY is using the template placeholder. Generate a secure key in .env.",
        UserWarning,
        stacklevel=2,
    )

# Vite dev mode: False by default so runserver works directly from built assets.
# Set VITE_DEV_MODE=true (e.g. via scripts/dev.ps1) when running vite dev server.
DJANGO_VITE["default"]["dev_mode"] = os.environ.get("VITE_DEV_MODE", "false").lower() == "true"

# Extend Content Security Policy for Vite development server
CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"] = list(
    CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"]
) + ["http://localhost:5173"]

CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"] = list(
    CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"]
) + ["http://localhost:5173", "ws://localhost:5173"]

# Plain staticfiles storage for local development and test execution without manifest compilation
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
