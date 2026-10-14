# Email Subsystem Setup & Inspection Guide

ELECTROCART includes a flexible email subsystem designed for zero-configuration local grading and high-throughput production dispatch.

---

## 1. Quick Start: Local Grading & Exam Mode (`file`)

By default, ELECTROCART runs in `file` email mode (`EMAIL_MODE=file`). **No SMTP credentials or internet connection are required for grading.**

When any user action triggers an email (registration confirmation, password reset, order invoice, refund notice):
1. The message is rendered as a standard RFC 5322 `.eml` file under `.emails/` with the recipient and timestamp in the filename:
   ```
   .emails/20261014_111543_faculty@university.edu_1.eml
   ```
2. You can inspect all outbound emails in the browser at:
   ```
   http://127.0.0.1:8000/dev/outbox/
   ```
3. **Faculty 30-Second Verification Workflow**:
   - Register a new account at `http://127.0.0.1:8000/accounts/signup/`.
   - On the "Verification Email Sent" screen, click the **Open Developer Outbox** link (or visit `/dev/outbox/`).
   - Click the top email addressed to your email.
   - Click the blue **Open Link** button next to the detected confirmation link.
   - Account email is confirmed and authenticated.

---

## 2. Dispatch Modes (`EMAIL_MODE`)

ELECTROCART supports three dispatch modes configured via the `EMAIL_MODE` environment variable in `.env`:

| Mode | Target Backend | Behavior | Best Used For |
| :--- | :--- | :--- | :--- |
| `file` *(default)* | `apps.core.email_backends.InspectableFileEmailBackend` | Writes `.eml` files to `.emails/` directory; viewable at `/dev/outbox/`. | University grading, offline review, testing. |
| `console` | `django.core.mail.backends.console.EmailBackend` | Dumps full MIME message to the running terminal stdout. | Quick headless terminal development. |
| `smtp` | `django.core.mail.backends.smtp.EmailBackend` | Connects to a standard TLS/SSL SMTP server. | Production deployments and live staging. |

---

## 3. Production SMTP Configurations

To switch to live email delivery, set `EMAIL_MODE=smtp` in `.env` and provide your provider credentials.

### A. Gmail / Google Workspace (App Password)

Google requires an **App Password** (standard account passwords will be rejected).
1. Go to your Google Account > **Security** > **2-Step Verification** > **App passwords**.
2. Create an App password for "ELECTROCART".
3. Add the following to your `.env`:

```env
EMAIL_MODE=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL="ELECTROCART <your_email@gmail.com>"
```

### B. Brevo (formerly Sendinblue)

1. Create a Brevo account and navigate to **Transactional** > **Settings** > **Configuration**.
2. Copy your SMTP Master Password and login.
3. Add to `.env`:

```env
EMAIL_MODE=smtp
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_brevo_login@domain.com
EMAIL_HOST_PASSWORD=your_brevo_smtp_key
DEFAULT_FROM_EMAIL="ELECTROCART <orders@yourverifieddomain.com>"
```

### C. Mailgun

1. In the Mailgun dashboard, select your domain under **Sending** > **Domains**.
2. Navigate to **Domain Settings** > **SMTP Credentials**.
3. Add to `.env`:

```env
EMAIL_MODE=smtp
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@mg.yourdomain.com
EMAIL_HOST_PASSWORD=your_mailgun_smtp_password
DEFAULT_FROM_EMAIL="ELECTROCART <support@mg.yourdomain.com>"
```

---

## 4. Diagnostic Management Command

To test your email configuration without triggering a website action, run:

```bash
python manage.py send_test_email --to=faculty@university.edu
```

### Example Output (`file` mode):
```text
Initiating test email dispatch:
  Recipient:    faculty@university.edu
  EMAIL_MODE:   file
  EMAIL_BACKEND: apps.core.email_backends.InspectableFileEmailBackend
  From:         Electrocart <noreply@electrocart.local>
SUCCESS: Successfully sent test email to <faculty@university.edu> (1 message(s) delivered).
Email written to .emails/ directory. Inspect at http://127.0.0.1:8000/dev/outbox/
```

If using `smtp` mode and a connection or credential error occurs, the command outputs the exact error response from the remote mail server.

---

## 5. Security Safeguards

- `/dev/outbox/` is strictly gated by `settings.DEBUG`. In production environments where `DEBUG=False`, accessing `/dev/outbox/` returns an immediate `404 Not Found`.
- Outbox file reading validates filenames with `os.path.basename` to prevent path traversal attacks.
- The `.emails/` directory is registered in `.gitignore` to prevent test messages or credentials from being committed to version control.
