"""
Developer outbox viewer (WP3.3) for local testing and exam grading.
Active only when settings.DEBUG is True.
"""

import email
from email import policy
import os
import re
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.html import escape


def dev_outbox(request):
    """
    Renders recent emails captured in the local .emails/ directory.
    Supports list view and detail view with HTML / plain-text inspection.
    """
    if not getattr(settings, "DEBUG", False):
        raise Http404("Outbox viewer is only available in DEBUG mode.")

    outbox_dir = Path(getattr(settings, "EMAIL_FILE_PATH", settings.BASE_DIR / ".emails"))
    outbox_dir.mkdir(parents=True, exist_ok=True)

    email_param = request.GET.get("email", "").strip()

    # Detail View
    if email_param:
        # Sanitize to prevent path traversal
        clean_filename = os.path.basename(email_param)
        file_path = outbox_dir / clean_filename
        if not file_path.is_file():
            raise Http404("Email file not found.")

        try:
            with open(file_path, "rb") as f:
                msg = email.message_from_binary_file(f, policy=policy.default)
        except Exception as e:
            return HttpResponse(f"Error reading email: {escape(str(e))}", status=500)

        subject = msg.get("Subject", "(No subject)")
        to_addr = msg.get("To", "(No recipient)")
        from_addr = msg.get("From", "(No sender)")
        date_str = msg.get("Date", "")

        text_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain" and not text_body:
                    text_body = part.get_content()
                elif ctype == "text/html" and not html_body:
                    html_body = part.get_content()
        else:
            if msg.get_content_type() == "text/html":
                html_body = msg.get_content()
            else:
                text_body = msg.get_content()

        # Extract confirmation or verification links
        urls = re.findall(r'https?://[^\s<>"]+|/[^\s<>"]+', text_body + "\n" + html_body)
        action_urls = [u for u in dict.fromkeys(urls) if any(k in u for k in ["confirm", "verify", "password/reset", "token"])]

        context = {
            "is_detail": True,
            "filename": clean_filename,
            "subject": subject,
            "to": to_addr,
            "from": from_addr,
            "date": date_str,
            "text_body": text_body,
            "html_body": html_body,
            "action_urls": action_urls,
        }
        return render(request, "core/dev_outbox.html", context)

    # List View
    emails = []
    files = sorted(outbox_dir.glob("*.eml"), key=lambda p: p.stat().st_mtime, reverse=True)
    # Also include .log files if any from legacy backend
    files.extend(sorted(outbox_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True))

    for fpath in files[:50]:
        try:
            with open(fpath, "rb") as f:
                msg = email.message_from_binary_file(f, policy=policy.default)
            emails.append({
                "filename": fpath.name,
                "timestamp": fpath.stat().st_mtime,
                "subject": msg.get("Subject", "(No subject)"),
                "to": msg.get("To", "(No recipient)"),
                "from": msg.get("From", ""),
                "size_bytes": fpath.stat().st_size,
            })
        except Exception:
            emails.append({
                "filename": fpath.name,
                "timestamp": fpath.stat().st_mtime,
                "subject": "(Unreadable message)",
                "to": "unknown",
                "from": "",
                "size_bytes": fpath.stat().st_size,
            })

    return render(
        request,
        "core/dev_outbox.html",
        {"is_detail": False, "emails": emails, "outbox_path": str(outbox_dir)},
    )
