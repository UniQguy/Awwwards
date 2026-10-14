"""
Tests for Contact Us customer inquiries and ContactMessage admin (WP7).
"""

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from apps.core.admin import ContactMessageAdmin
from apps.core.models import ContactMessage

User = get_user_model()


class ContactTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_contact_get_renders_form(self):
        """GET /contact/ returns HTTP 200 with contact form elements."""
        resp = self.client.get(reverse("contact"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Contact Customer Care")
        self.assertContains(resp, "Send a Message")
        self.assertContains(resp, "care@electrocart.local")

    def test_contact_post_creates_message_and_redirects(self):
        """Valid POST to /contact/ persists ContactMessage and displays confirmation."""
        data = {
            "name": "Priyanshu Sharma",
            "email": "priyanshu@example.com",
            "subject": "Inquiry about studio monitor impedance",
            "message": "Do the Flow studio monitors include balanced TRS inputs?",
        }
        resp = self.client.post(reverse("contact"), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Thank you for reaching out")

        # Verify DB entry
        msg = ContactMessage.objects.filter(email="priyanshu@example.com").first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.name, "Priyanshu Sharma")
        self.assertEqual(msg.subject, "Inquiry about studio monitor impedance")
        self.assertFalse(msg.resolved)

    def test_contact_post_missing_fields_validation(self):
        """POST with empty fields does not create record and shows error."""
        data = {
            "name": "",
            "email": "",
            "subject": "",
            "message": "",
        }
        resp = self.client.post(reverse("contact"), data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Please provide your name")
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_admin_registration_and_actions(self):
        """ContactMessage is registered in admin with functional actions."""
        self.assertIn(ContactMessage, site._registry)
        model_admin = site._registry[ContactMessage]
        self.assertIsInstance(model_admin, ContactMessageAdmin)

        msg = ContactMessage.objects.create(
            name="Test User",
            email="test@example.com",
            subject="Test Admin",
            message="Testing admin actions",
            resolved=False,
        )

        # Exercise mark_resolved action
        model_admin.mark_resolved(None, ContactMessage.objects.filter(id=msg.id))
        msg.refresh_from_db()
        self.assertTrue(msg.resolved)

        # Exercise mark_unresolved action
        model_admin.mark_unresolved(None, ContactMessage.objects.filter(id=msg.id))
        msg.refresh_from_db()
        self.assertFalse(msg.resolved)
