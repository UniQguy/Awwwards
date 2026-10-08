"""
Unit tests enforcing copy honesty, plain voice, and absence of marketing hype.
Tests audit_copy_honesty against all templates.
"""

from django.test import SimpleTestCase
from scripts.audit_copy_honesty import audit_templates


class CopyHonestyTestCase(SimpleTestCase):
    def test_copy_honesty_audit_passes(self):
        """Templates must contain zero banned marketing words, zero schema review spam, and zero customer-facing exclamations."""
        passed = audit_templates()
        self.assertTrue(passed, "Copy and honesty audit failed. Check banned words and unverified claims.")
