"""
Tests for Real Email Subsystem (R7 Item 2):
- Masked confirmation notice on verification_sent page
- Resend confirmation button and action
- send_test_email missing credential error in smtp mode
- FallbackSmtpFileEmailBackend dual dispatch
- End-to-end signup -> outbox inspection -> confirm -> login flow
"""

import os
import re
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from allauth.account.models import EmailAddress, EmailConfirmation
from apps.accounts.views import mask_email

User = get_user_model()


class RealEmailSubsystemTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_mask_email_utility(self):
        """Validates email masking for various username lengths."""
        self.assertEqual(mask_email("faculty@university.edu"), "fa***y@university.edu")
        self.assertEqual(mask_email("john.doe@example.com"), "jo***e@example.com")
        self.assertEqual(mask_email("ab@domain.com"), "a***@domain.com")
        self.assertEqual(mask_email("a@domain.com"), "a***@domain.com")
        self.assertEqual(mask_email("invalid-email"), "invalid-email")

    def test_signup_shows_masked_email_and_resend_notice(self):
        """After signup, the page shows the exact prompt copy with masked email and Resend button."""
        signup_url = reverse("account_signup")
        email = "professor.grading@university.edu"
        password = "ExamPassword123!"

        resp = self.client.post(
            signup_url,
            {
                "email": email,
                "password1": password,
                "password2": password,
            },
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")

        # Must show plain message with masked email
        expected_masked = mask_email(email)
        self.assertIn("We sent a confirmation link to", content)
        self.assertIn(expected_masked, content)
        self.assertIn("If it does not arrive, check spam or use Resend.", content)

        # Resend confirmation button must be visible
        self.assertIn("Resend confirmation", content)
        self.assertIn(reverse("account_resend_verification_email"), content)

    def test_resend_confirmation_triggers_dispatch(self):
        """POSTing to resend verification email triggers another confirmation email."""
        email = "resend.test@university.edu"
        user = User.objects.create_user(email=email, password="Password123!")
        EmailAddress.objects.create(user=user, email=email, primary=True, verified=False)

        # Set email in session as done during registration
        session = self.client.session
        session["account_verification_email"] = email
        session.save()

        resend_url = reverse("account_resend_verification_email")
        resp = self.client.post(resend_url, {"email": email}, follow=True)

        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        self.assertIn("A new confirmation link has been sent", content)

    @override_settings(
        EMAIL_MODE="smtp",
        EMAIL_HOST_USER="",
        EMAIL_HOST_PASSWORD="",
    )
    def test_send_test_email_smtp_credentials_missing_error(self):
        """send_test_email raises a clear CommandError if SMTP credentials are missing."""
        with self.assertRaises(CommandError) as ctx:
            call_command("send_test_email", to="test@example.com")
        self.assertIn("SMTP credentials missing", str(ctx.exception))

    @override_settings(EMAIL_BACKEND="apps.core.email_backends.InspectableFileEmailBackend")
    def test_e2e_signup_outbox_confirm_and_login_flow(self):
        """With EMAIL_MODE=file, full flow: signup -> open outbox -> confirm -> log in."""
        email = "e2e_student@university.edu"
        password = "StudentPassword123!"

        # 1. Signup
        signup_resp = self.client.post(
            reverse("account_signup"),
            {
                "email": email,
                "password1": password,
                "password2": password,
            },
            follow=True,
        )
        self.assertEqual(signup_resp.status_code, 200)

        # 2. Extract confirmation URL from the outbox .eml file
        from django.conf import settings
        from pathlib import Path
        email_dir = Path(settings.BASE_DIR) / ".emails"
        eml_files = sorted(email_dir.glob(f"*{email}*.eml"), key=os.path.getmtime)
        self.assertTrue(len(eml_files) > 0, "Outbox email must be written.")

        with open(eml_files[-1], "r", encoding="utf-8", errors="ignore") as f:
            eml_content = f.read()

        match = re.search(r"/accounts/confirm-email/[^/\s\)\"\'>]+/", eml_content)
        self.assertIsNotNone(match, "Confirmation URL must be present in outbound email.")
        confirm_path = match.group(0)

        # 3. Simulate clicking the confirmation link from the outbox / email
        confirm_resp = self.client.get(confirm_path, follow=True)
        self.assertEqual(confirm_resp.status_code, 200)

        # If confirm page requires POST to confirm (allauth standard):
        if "confirm" in confirm_resp.content.decode("utf-8").lower():
            post_confirm_resp = self.client.post(confirm_path, follow=True)
            self.assertEqual(post_confirm_resp.status_code, 200)

        # 4. Check email is now verified
        email_record = EmailAddress.objects.get(email=email)
        self.assertTrue(email_record.verified)

        # 5. Log in
        login_resp = self.client.post(
            reverse("account_login"),
            {
                "login": email,
                "password": password,
            },
            follow=True,
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.context["user"].is_authenticated)
        self.assertEqual(login_resp.context["user"].email, email)

    def test_fallback_smtp_file_backend_preserves_file_on_smtp_error(self):
        """When DEMO_EMAIL_FALLBACK=True, a failure in SMTP still writes the outbox .eml file."""
        from django.core.mail import EmailMessage
        from apps.core.email_backends import FallbackSmtpFileEmailBackend
        from pathlib import Path

        backend = FallbackSmtpFileEmailBackend()
        # Mock smtp_backend.send_messages to simulate network timeout / connection refused
        def failing_smtp(msgs):
            raise ConnectionRefusedError("Simulated venue network block (port 587 unreachable)")

        backend.smtp_backend.send_messages = failing_smtp

        test_email = "network_blocked_faculty@university.edu"
        msg = EmailMessage(
            subject="Venue Network Block Test",
            body="This email was mirrored to outbox despite SMTP failure.",
            from_email="noreply@electrocart.local",
            to=[test_email],
        )

        with self.settings(DEMO_EMAIL_FALLBACK=True):
            delivered = backend.send_messages([msg])
            self.assertEqual(delivered, 1)

        # Assert file was written
        email_dir = Path(settings.BASE_DIR) / ".emails"
        eml_files = list(email_dir.glob(f"*{test_email}*.eml"))
        self.assertTrue(len(eml_files) > 0, "Outbox file must be written even when SMTP is blocked.")

