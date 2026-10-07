"""
Production Django settings for ELECTROCART.
Strict security hardening conforming to check --deploy invariants.
"""

import os
from django.core.exceptions import ImproperlyConfigured
from .base import *

# In production, DEBUG must strictly be False
DEBUG = False

# SELLER_STATE is statutory requirement for Indian GST invoicing
if not SELLER_STATE:
    raise ImproperlyConfigured(
        "SELLER_STATE environment variable is required in production for Indian GST compliance."
    )

# Security and SSL Hardening
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy SSL Header (when deployed behind reverse proxy / load balancer)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cross-Origin Policies
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Production storage: WhiteNoise compressed manifest static files
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
