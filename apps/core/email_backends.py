"""
Custom inspectable file email backend for ELECTROCART (WP3.2).
Writes each email message to .emails/<timestamp>_<recipient>.eml for faculty exam review.
"""

import datetime
import logging
import os
import re
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend

logger = logging.getLogger(__name__)


class InspectableFileEmailBackend(BaseEmailBackend):
    """
    Saves sent emails as standalone .eml RFC 5322 files in EMAIL_FILE_PATH.
    Files are named <YYYYMMDD_HHMMSS>_<recipient>.eml.
    """

    def __init__(self, file_path=None, **kwargs):
        super().__init__(**kwargs)
        self.file_path = str(file_path or getattr(settings, "EMAIL_FILE_PATH", os.path.join(settings.BASE_DIR, ".emails")))
        os.makedirs(self.file_path, exist_ok=True)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        num_sent = 0
        for idx, message in enumerate(email_messages):
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                recipients = "_".join(re.sub(r"[^a-zA-Z0-9@._-]", "", r) for r in (message.to or ["norecipient"]))[:40]
                filename = f"{timestamp}_{recipients}_{idx+1}.eml"
                filepath = os.path.join(self.file_path, filename)
                with open(filepath, "wb") as f:
                    f.write(message.message().as_bytes())
                num_sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return num_sent


class FallbackSmtpFileEmailBackend(BaseEmailBackend):
    """
    Dual-dispatch email backend for DEMO_EMAIL_FALLBACK=1:
    1. Writes an inspectable .eml file to .emails/ for /dev/outbox/ access.
    2. Attempts live SMTP dispatch. If the venue network or credentials reject SMTP,
       the failure is logged and the file copy in /dev/outbox/ ensures uninterrupted grading.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.file_backend = InspectableFileEmailBackend(fail_silently=fail_silently)
        self.smtp_backend = SmtpEmailBackend(fail_silently=fail_silently, **kwargs)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        # 1. Always record in local file outbox
        file_count = self.file_backend.send_messages(email_messages)

        # 2. Attempt live SMTP delivery
        try:
            smtp_count = self.smtp_backend.send_messages(email_messages)
            logger.info("Dispatched %d message(s) via SMTP and mirrored to .emails/ outbox.", smtp_count)
            return smtp_count
        except Exception as exc:
            logger.warning(
                "SMTP dispatch failed (%s). Retained file copy in .emails/ for /dev/outbox/ inspection.",
                exc,
            )
            if not getattr(settings, "DEMO_EMAIL_FALLBACK", False) and not self.fail_silently:
                raise
            return file_count

