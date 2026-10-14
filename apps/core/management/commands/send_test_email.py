"""
Management command to send a test email through the active EMAIL_BACKEND (WP3.4).
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Dispatches a test email via the configured EMAIL_BACKEND to verify delivery settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            type=str,
            required=True,
            help="Recipient email address for the diagnostic test message.",
        )
        parser.add_argument(
            "--subject",
            type=str,
            default="ELECTROCART Test Email Notification",
            help="Optional custom subject line.",
        )

    def handle(self, *args, **options):
        recipient = options["to"].strip()
        subject = options["subject"].strip()

        mode = getattr(settings, "EMAIL_MODE", "file")
        backend = getattr(settings, "EMAIL_BACKEND", "")
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@electrocart.local")

        self.stdout.write(f"Initiating test email dispatch:")
        self.stdout.write(f"  Recipient:    {recipient}")
        self.stdout.write(f"  EMAIL_MODE:   {mode}")
        self.stdout.write(f"  EMAIL_BACKEND: {backend}")
        self.stdout.write(f"  From:         {from_email}")

        now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        text_content = (
            f"ELECTROCART Email Subsystem Diagnostic\n"
            f"-----------------------------------------\n"
            f"This is an automated verification message sent at {now_str}.\n\n"
            f"Backend: {backend}\n"
            f"Mode:    {mode}\n"
            f"Target:  {recipient}\n\n"
            f"If you received this in .emails/ or your inbox, your email subsystem is operating correctly.\n"
        )

        html_content = f"""
        <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #0f172a; margin-top: 0;">ELECTROCART Email Diagnostic</h2>
            <p style="color: #334155;">This is an automated verification message dispatched at <strong>{now_str}</strong>.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; font-weight: 600; color: #64748b;">Backend</td><td style="padding: 8px 0; font-family: monospace;">{backend}</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; font-weight: 600; color: #64748b;">Mode</td><td style="padding: 8px 0;">{mode}</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 8px 0; font-weight: 600; color: #64748b;">Recipient</td><td style="padding: 8px 0;">{recipient}</td></tr>
            </table>
            <p style="color: #166534; background: #f0fdf4; padding: 12px; border-radius: 4px; font-size: 13px;">
                Status: Email subsystem operational.
            </p>
        </div>
        """

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient],
            )
            msg.attach_alternative(html_content, "text/html")
            sent = msg.send(fail_silently=False)

            if sent > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"SUCCESS: Successfully sent test email to <{recipient}> ({sent} message(s) delivered)."
                    )
                )
                if mode == "file":
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Email written to .emails/ directory. Inspect at http://127.0.0.1:8000/dev/outbox/"
                        )
                    )
            else:
                raise CommandError(f"Dispatch failed: send() returned {sent}")

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"ERROR: Failed to dispatch test email: {exc}"))
            raise CommandError(str(exc))
