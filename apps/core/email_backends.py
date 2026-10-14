"""
Custom inspectable file email backend for ELECTROCART (WP3.2).
Writes each email message to .emails/<timestamp>_<recipient>.eml for faculty exam review.
"""

import datetime
import os
import re
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


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
