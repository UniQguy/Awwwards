# Deployment Readiness Guide
**ELECTROCART Monograph Storefront**  
*System Architecture, Production Hardening, and Deployment Runbook*

---

## 1. System Architecture Overview

ELECTROCART is engineered as a monolithic Twelve-Factor Django application with a decoupled, high-performance modern frontend build pipeline. It is architected for single-server bare-metal/VPS deployment or containerized Kubernetes/Docker deployment.

```mermaid
flowchart TD
    Client["Client Browser / Mobile Viewport"]
    Proxy["Nginx / Caddy (TLS Termination, HTTP/2, Gzip/Brotli)"]
    WSGI["Gunicorn / Uvicorn (Django 5.x WSGI/ASGI Application)"]
    DB[("PostgreSQL 16 / SQLite (Demo)")]
    Cache[("Redis 7 (Sessions, Cache, Rate Limits)")]
    Storage[("Object Storage: AWS S3 / Cloudflare R2 (Media)")]
    Payment["Razorpay Gateway (UPI, Cards, Netbanking)"]
    Email["Amazon SES / SendGrid (Transactional SMTP)"]

    Client -->|HTTPS / WSS| Proxy
    Proxy -->|Static Files /static/| Proxy
    Proxy -->|Reverse Proxy :8000| WSGI
    WSGI -->|Queries / ORM| DB
    WSGI -->|Cache & Rate Limits| Cache
    WSGI -->|Signed Uploads / CDN| Storage
    WSGI -->|Webhooks / API| Payment
    WSGI -->|RFC 5322 Emails| Email
```

---

## 2. Infrastructure Prerequisites

| Component | Minimum Specification | Production Recommendation |
| :--- | :--- | :--- |
| **Compute** | 1 vCPU, 1 GB RAM | 2 vCPU, 4 GB RAM (supports 500+ req/sec) |
| **Operating System**| Ubuntu 22.04 LTS / Debian 12 | Ubuntu 24.04 LTS |
| **Python** | Python 3.12+ | Python 3.12.7+ |
| **Node.js** | Node.js 18+ | Node.js 20 LTS (Active) |
| **Database** | SQLite 3.40+ (Demo) | PostgreSQL 16+ |
| **Cache** | LocMem (Demo) | Redis 7+ |
| **Reverse Proxy** | None (Local runserver) | Nginx 1.24+ or Caddy 2.8+ |

---

## 3. Environment Configuration (`.env.production`)

A production deployment must populate all critical keys. Never commit `.env.production` to version control.

```bash
# Core Django
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=generate_with_django_core_management_utils_get_random_secret_key
DEBUG=False
ALLOWED_HOSTS=electrocart.in,www.electrocart.in,127.0.0.1

# Database Configuration
DATABASE_URL=postgres://electrocart_user:StrongPassword123@127.0.0.1:5432/electrocart_prod

# Cache & Rate Limiting
REDIS_URL=redis://127.0.0.1:6379/1

# Email Delivery
EMAIL_MODE=smtp
EMAIL_HOST=email-smtp.ap-south-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=AKIAEXAMPLEKEY
EMAIL_HOST_PASSWORD=SecretSmtpPassword
DEFAULT_FROM_EMAIL=ELECTROCART Customer Care <care@electrocart.in>

# Payment Gateway (Razorpay)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=live_secret_xxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=live_webhook_secret_xxxxxx

# Admin & Demo Controls
ADMIN_URL=ops-control-panel-9f2/
SHOW_PLACEHOLDER_LABELS=False
```

---

## 4. Build and Static Asset Pipeline

ELECTROCART does not serve unminified raw assets in production. The build pipeline compiles modern CSS custom properties, responsive typography tokens, and JavaScript modules.

```bash
# 1. Install Node.js dependencies
npm ci

# 2. Compile CSS tokens, typography, and JS bundles
npm run build

# 3. Collect static files into STATIC_ROOT
python manage.py collectstatic --noinput --clear
```

Static assets are versioned and compressed via WhiteNoise / Nginx with permanent cache headers:
```http
Cache-Control: public, max-age=31536000, immutable
```

---

## 5. Database Setup & Migrations

```bash
# 1. Run database schema migrations
python manage.py migrate --noinput

# 2. Verify migration consistency
python manage.py makemigrations --check

# 3. For initial deployment, seed categories and catalogue
python manage.py seed_categories
python manage.py import_products data/products_catalog.csv
```

---

## 6. WSGI / Systemd Service Configuration

Create `/etc/systemd/system/electrocart.service`:

```ini
[Unit]
Description=ELECTROCART Monograph Storefront Gunicorn Daemon
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/electrocart
EnvironmentFile=/var/www/electrocart/.env.production
ExecStart=/var/www/electrocart/.venv/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --worker-tmp-dir /dev/shm \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/electrocart/access.log \
    --error-logfile /var/log/electrocart/error.log \
    --capture-output \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable electrocart
sudo systemctl start electrocart
```

---

## 7. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/electrocart.conf`:

```nginx
# HTTP - Redirect all traffic to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name electrocart.in www.electrocart.in;
    return 301 https://$host$request_uri;
}

# HTTPS - Monograph Storefront
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name electrocart.in www.electrocart.in;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/electrocart.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/electrocart.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Static Assets (Direct Nginx Serving)
    location /static/ {
        alias /var/www/electrocart/staticfiles/;
        expires 365d;
        access_log off;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Uploaded Media
    location /media/ {
        alias /var/www/electrocart/media/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # Application Reverse Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # Health Check (Internal Monitoring)
    location = /health/ {
        proxy_pass http://127.0.0.1:8000/health/;
        access_log off;
    }
}
```

---

## 8. Security Hardening & Pre-Flight Checks

Before opening port 443 to public traffic:

1. **Django Deployment Checklist**:
   ```bash
   python manage.py check --deploy --settings=config.settings.production
   ```
   *Expected output: `System check identified no issues (0 silenced)`.*

2. **Database Integrity**:
   ```bash
   python scripts/db_summary.py
   ```
   *Verifies zero foreign key violations and intact index structures.*

3. **Offline & CDN Independence**:
   ```bash
   python scripts/offline_check.py
   ```
   *Confirms the application has zero external CDN runtime dependencies.*

4. **Rate Limit Verification**:
   Verify endpoints `/checkout/place/`, `/shipping/check/`, `/search/`, and `/cart/coupon/apply/` enforce HTTP 429 throttling on rapid bursts.

---

## 9. Backup & Disaster Recovery Procedures

### Database Backup
```bash
# PostgreSQL automated backup
pg_dump -U electrocart_user -Fc electrocart_prod > /backups/db/electrocart_$(date +%Y%m%d_%H%M%S).dump

# SQLite backup (if using file database)
python manage.py db_backup
```

### Database Restore
```bash
# PostgreSQL restore
pg_restore -U electrocart_user -d electrocart_prod --clean /backups/db/electrocart_backup.dump
```
