#!/usr/bin/env python3
"""
Electrocart Settings & Infrastructure Validation Script.
Verifies that Django boots with config.settings.local, all settings are valid,
and system checks pass.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
from django.core.management import call_command
from django.db import connections

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

try:
    django.setup()
    print("Django setup successful.")
    print("Verifying database connection...")
    connections["default"].ensure_connection()
    print("Database connection successful.")
    print("Running system checks...")
    call_command("check")
    print("\nSettings & System Check: PASSED")
    sys.exit(0)
except Exception as exc:
    print(f"\nSettings & System Check FAILED: {exc}", file=sys.stderr)
    sys.exit(1)
