# Production Environment, Configuration & Operations Guide

## 1. Environment Variable Reference Table

| Variable Name | Required? | Secret? | Default Value | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SECRET_KEY` | **Required** | **YES** | None (raises error if unset) | `django-insecure-6ewnr...` | Cryptographic signing key for sessions, CSRF, and signed tokens. |
| `DEBUG` | Optional | No | `False` (in base/prod), `True` (local) | `false` | Enable/disable verbose debugging screens. Must be `false` in production. |
| `DATABASE_URL` | **Required** | **YES** | None (raises error if unset) | `sqlite:///data/db.sqlite3` or `postgres://u:p@db:5432/app` | Database connection string formatted for `dj_database_url`. |
| `ALLOWED_HOSTS` | **Required** | No | `localhost,127.0.0.1` | `electrocart.in,www.electrocart.in` | Comma-separated list of valid host/domain names. |
| `CSRF_TRUSTED_ORIGINS` | **Required** | No | `""` | `https://electrocart.in,https://www.electrocart.in` | Trusted origins for state-mutating CSRF requests. |
| `SITE_URL` | Optional | No | `http://localhost:8000` | `https://electrocart.in` | Canonical base URL used for sitemap, emails, and full link generation. |
| `ADMIN_URL` | Optional | No | `admin/` | `management-k9x/` | Custom URL prefix for Django admin to prevent automated bot scanning. |
| `SELLER_STATE` | **Required** | No | `""` (raises error in prod) | `Karnataka` | Origin state for Indian GST split (IGST vs CGST/SGST). |
| `SELLER_GSTIN` | Optional | No | `""` | `29ABCDE1234F1Z5` | 15-digit GST identification number. When omitted, invoices issue as Bill of Supply. |
| `SELLER_LEGAL_NAME` | Optional | No | `""` | `Electrocart Retail LLP` | Statutory company name printed on invoices and legal documents. |
| `SELLER_ADDRESS` | Optional | No | `""` | `100 MG Road, Bengaluru 560001` | Statutory registered company address. |
| `RAZORPAY_KEY_ID` | Optional | No | `""` | `rzp_live_abcdef1234` | Razorpay public API key for modal checkout. |
| `RAZORPAY_KEY_SECRET` | Optional | **YES** | `""` | `live_secret_key_9876` | Razorpay secret key for payment capture and signature verification. |
| `RAZORPAY_WEBHOOK_SECRET` | Optional | **YES** | `""` | `wh_secret_xyz123` | Secret token used to verify inbound Razorpay webhook HMAC signatures. |
| `EMAIL_BACKEND` | Optional | No | `django.core.mail.backends.console.EmailBackend` | `django.core.mail.backends.smtp.EmailBackend` | Mail backend engine (console, SMTP, or third-party API adapter). |
| `EMAIL_HOST` | Optional | No | `localhost` | `smtp.postmarkapp.com` | SMTP relay server host. |
| `EMAIL_PORT` | Optional | No | `587` | `587` | SMTP server port. |
| `EMAIL_USE_TLS` | Optional | No | `True` | `true` | Enforce STARTTLS for SMTP transmission. |
| `EMAIL_HOST_USER` | Optional | **YES** | `""` | `postmark-api-token` | SMTP authentication username. |
| `EMAIL_HOST_PASSWORD` | Optional | **YES** | `""` | `secret-smtp-password` | SMTP authentication password. |
| `DEFAULT_FROM_EMAIL` | Optional | No | `Electrocart <noreply@electrocart.local>` | `Electrocart Orders <orders@electrocart.in>` | Sender address for transactional emails. |
| `BACKUP_DIR` | Optional | No | `BASE_DIR / "backups"` | `/var/backups/electrocart` | Destination folder for `python manage.py db_backup`. |
| `BACKUP_RETENTION` | Optional | No | `7` | `14` | Number of backup archives to retain before pruning old copies. |
| `SECURE_SSL_REDIRECT` | Optional | No | `True` (in production.py) | `true` | Redirect all HTTP requests to HTTPS. |
| `MOTION_DEBUG` | Optional | No | `False` | `false` | Enable dev-only `?motion=1|2|3` query param override. |

---

## 2. Build Pipeline & Deployment Steps

### Step 1: Install Dependencies
```bash
python -m pip install -r requirements-prod.txt
npm ci
```

### Step 2: Compile Front-End Assets
```bash
npm run build
```
Generates production hashed CSS and JavaScript bundles into `static/dist/` with a manifest file at `static/dist/.vite/manifest.json`.

### Step 3: Collect Static Files
```bash
python manage.py collectstatic --no-input
```
WhiteNoise compresses assets with gzip and brotli and prepares the manifest storage.

### Step 4: Run Database Migrations
```bash
python manage.py migrate --no-input
```

### Step 5: Verify Deployment Readiness
```bash
python manage.py check --deploy --settings=config.settings.production
```

---

## 3. First-Deploy Checklist

- [ ] **Generate Secrets**: Set unique, random `SECRET_KEY` ($\ge 50$ characters).
- [ ] **Set Legal & Seller Details**: Declare `SELLER_STATE` (required), `SELLER_GSTIN`, `SELLER_LEGAL_NAME`, and `SELLER_ADDRESS`.
- [ ] **Configure Host Security**: Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the exact production domain(s).
- [ ] **Configure Reverse Proxy**: Ensure Nginx / Traefik / ALB forwards `X-Forwarded-Proto: https` so `SECURE_PROXY_SSL_HEADER` functions properly.
- [ ] **Obtain Live Razorpay Keys**: Add `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET`. Register the webhook URL `https://yourdomain.com/payments/razorpay/webhook/` in the Razorpay dashboard for payment events.
- [ ] **Configure Mail Server**: Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` with real provider credentials (Postmark, SES, Sendgrid).
- [ ] **Run Initial Seed / Import**: If initializing fresh instance, run:
  ```bash
  python manage.py import_catalog data/electronics_product.csv
  python manage.py seed_demo
  ```
- [ ] **Create Superuser**: Run `python manage.py createsuperuser` to provision first administrator.

---

## 4. Scheduled Tasks & Automation (Cron / Scheduler)

Configure the following recurring jobs in your system cron or container scheduler:

### 1. Cleanup Expired Stock Reservations (Every 5 minutes)
Frees up inventory held by abandoned checkout sessions whose 15-minute TTL has lapsed:
```cron
*/5 * * * * cd /path/to/electrocart && .venv/bin/python manage.py cleanup_expired_reservations >> /var/log/electrocart-cleanup.log 2>&1
```

### 2. SQLite Online Database Backup (Daily at 03:00 AM)
Takes a non-blocking snapshot using SQLite's online backup API, retaining 7 days of archives:
```cron
0 3 * * * cd /path/to/electrocart && .venv/bin/python manage.py db_backup --retention=7 >> /var/log/electrocart-backup.log 2>&1
```

### 3. Clear Expired Sessions (Daily at 04:00 AM)
Prunes expired session records from the database:
```cron
0 4 * * * cd /path/to/electrocart && .venv/bin/python manage.py clearsessions >> /var/log/electrocart-sessions.log 2>&1
```

---

## 5. Production Reality Check: SQLite vs. PostgreSQL

### SQLite Limits & Operational Profile
- **Single-Writer Concurrency**: SQLite locks the database file during write transactions. In WAL mode (`PRAGMA journal_mode=WAL;`), readers never block writers and writers never block readers, making SQLite suitable for storefront traffic with up to 50–100 concurrent requests.
- **Backups**: Never copy `db.sqlite3` while a write is occurring. Always execute `python manage.py db_backup` which leverages `sqlite3.Connection.backup` to read consistent page snapshots.
- **When to Migrate to PostgreSQL**:
  1. Multiple horizontally scaled web app servers behind a load balancer.
  2. Sustained checkout mutation concurrency exceeding 50 writes/second.
  3. Requirement for point-in-time continuous WAL streaming (e.g., AWS RDS or Fly Postgres).

### Migration Procedure
1. Set `DATABASE_URL=postgres://user:password@host:5432/dbname` in `.env`.
2. Install psycopg binary: `pip install psycopg[binary,pool]`.
3. Run `python manage.py migrate`.
4. Re-run `import_catalog` or restore PostgreSQL dump.
