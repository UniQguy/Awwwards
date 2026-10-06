"""
Local development settings for ELECTROCART.
"""

import warnings
from .base import *

DEBUG = True

# Allow testserver and localhost for testing
ALLOWED_HOSTS = list(ALLOWED_HOSTS) + ["testserver"]

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

# Enable Vite dev server integration in local mode
DJANGO_VITE["default"]["dev_mode"] = True

# Extend Content Security Policy for Vite development server
CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"] = list(
    CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"]
) + ["http://localhost:5173"]

CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"] = list(
    CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"]
) + ["http://localhost:5173", "ws://localhost:5173"]
