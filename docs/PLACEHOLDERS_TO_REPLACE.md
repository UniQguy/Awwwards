# Production Readiness Checklist: Placeholders to Replace
**ELECTROCART Monograph Storefront**  
*Academic Project Evaluation & Production Cutover Guide*

---

## 1. Overview & Demonstration Notice

ELECTROCART is structured as an academically rigorous, zero-dependency e-commerce platform built for evaluation by university faculty. All mock entities, illustrative legal registrations, and demonstration credentials in local development are strictly isolated and clearly flagged.

Before deploying this software into a live commercial environment with real financial transactions and statutory obligations, the items in this checklist must be provisioned and configured.

---

## 2. Production Cutover Checklist

### A. Payment Gateway Credentials
Currently, the application runs with mock Razorpay payment workflows and test webhook verification.
- [ ] **Razorpay Key ID**: Replace `RAZORPAY_KEY_ID` with live production key from Razorpay Dashboard (`rzp_live_...`).
- [ ] **Razorpay Key Secret**: Replace `RAZORPAY_KEY_SECRET` with live production secret.
- [ ] **Razorpay Webhook Secret**: Configure webhook endpoint `https://<domain>/payments/razorpay/webhook/` in Razorpay Dashboard and set `RAZORPAY_WEBHOOK_SECRET`.
- [ ] **Payment Methods**: Enable UPI (Google Pay, PhonePe, Paytm), Netbanking, Credit/Debit Cards, and EMI in payment gateway settings.

### B. Statutory Tax & GST Configuration
All invoices and credit notes currently print educational demonstration registration numbers (`GSTIN: 29AAAAA0000A1Z5` - Karnataka demo format).
- [ ] **Legal Business Name**: Set registered entity name (e.g., `ELECTROCART RETAIL PRIVATE LIMITED`).
- [ ] **State of Registration**: Verify home state (default: Karnataka, State Code `29`) for CGST + SGST vs. IGST intra-state / inter-state calculation.
- [ ] **Live GSTIN**: Enter official 15-character Goods and Services Tax Identification Number.
- [ ] **HSN / SAC Codes**: Verify catalog product HSN codes (e.g., `8518` for audio equipment, `8517` for phones, `8544` for cables) with accounting counsel.
- [ ] **Invoice Sequencing**: Configure state-compliant sequential fiscal year numbering format (e.g., `EC/2026-27/00001`).

### C. Legal & Regulatory Identity
All legal pages (`/legal/terms/`, `/legal/privacy/`, `/legal/shipping/`, `/legal/refunds/`) contain university evaluation disclaimers that must be updated with corporate particulars.
- [ ] **Registered Office Address**: Replace Bengaluru demonstration address with corporate registered office.
- [ ] **Statutory Grievance Officer**: Nominate a designated Grievance Officer per the Indian *Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021* and *Consumer Protection (E-Commerce) Rules, 2020*.
  - Name, Designation, Physical Address, Direct Email, Escalation Phone.
- [ ] **Customer Care Contacts**: Replace `care@electrocart.in` and `+91 (080) 2345-6789` with verified corporate helpdesk channels.
- [ ] **Return Window & Policy**: Confirm physical return inspection duration (currently configured as 14 statutory days with serial verification).

### D. Carrier & Shipping Logistics
Delivery estimates are currently computed against Indian PIN code regexes and local speed tables.
- [ ] **Carrier Integration**: Connect real logistics API (e.g., Shiprocket, Delhivery, Blue Dart) in `apps/shipping/services/`.
- [ ] **Live PIN Serviceability**: Connect automated PIN code serviceable database / API feed.
- [ ] **Automated Manifests & AWB**: Implement real-time airway bill (AWB) generation upon order state transition to `SHIPPED`.
- [ ] **Reverse Logistics**: Configure carrier return pickup routing for approved return requests.

### E. Transactional Email Infrastructure
Transactional notifications (order confirmations, shipping notices, credit note PDFs) currently use `InspectableFileEmailBackend` storing `.eml` files in `.emails/` for evaluation.
- [ ] **Email Provider**: Set `EMAIL_MODE=smtp` in environment.
- [ ] **SMTP Credentials**: Configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS`.
- [ ] **Sender Authentication**: Configure DNS records on the production domain:
  - **SPF**: `v=spf1 include:_spf.example.com ~all`
  - **DKIM**: 2048-bit cryptographic key signing for `care@electrocart.in`
  - **DMARC**: `v=DMARC1; p=reject; rua=mailto:dmarc@electrocart.in`

### F. Domain, SSL/TLS, and Web Security
- [ ] **Production Domain**: Set `ALLOWED_HOSTS` to production domains (e.g., `electrocart.in`, `www.electrocart.in`).
- [ ] **SSL/TLS Certificates**: Provision Let's Encrypt or corporate TLS 1.3 certificates. Enforce HSTS (`SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`, `SECURE_HSTS_PRELOAD=True`).
- [ ] **Secure Cookies**: Ensure `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` are active (automatically enforced in `config.settings.production`).
- [ ] **Reverse Proxy**: Configure Nginx or Caddy with proxy headers (`X-Forwarded-For`, `X-Forwarded-Proto`).
- [ ] **Rate Limiting Cache**: Set `REDIS_URL` for distributed rate limiting in `django-ratelimit`.

### G. Static and Media Storage
- [ ] **Static Assets**: Run `npm run build && python manage.py collectstatic --noinput`.
- [ ] **Media Bucket**: Configure AWS S3, Cloudflare R2, or Google Cloud Storage for user-uploaded product images using `django-storages`.
- [ ] **Sentry DSN**: Configure `SENTRY_DSN` for real-time unhandled exception tracking.

---

## 3. Environment Variables Audit Reference

| Variable Name | Academic / Demo Value | Production Requirement |
| :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.local` | `config.settings.production` |
| `SECRET_KEY` | Development insecure string | High-entropy 64+ char random secret from vault |
| `DEBUG` | `True` | `False` (CRITICAL) |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | `electrocart.in,www.electrocart.in` |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | `postgres://user:pass@host:5432/electrocart` |
| `EMAIL_MODE` | `file` (writes to `.emails/`) | `smtp` |
| `EMAIL_HOST` | `None` | `smtp.sendgrid.net` / `email-smtp.ap-south-1.amazonaws.com` |
| `RAZORPAY_KEY_ID` | Mock / Test ID | Live Merchant Key ID |
| `RAZORPAY_KEY_SECRET` | Mock / Test Secret | Live Merchant Secret |
| `RAZORPAY_WEBHOOK_SECRET` | Mock Secret | Live Merchant Webhook Secret |
| `REDIS_URL` | `None` (locmem cache) | `redis://127.0.0.1:6379/1` |
| `ADMIN_URL` | `admin/` | Custom obscure path (e.g. `ops-portal-9f2/`) |
| `SHOW_PLACEHOLDER_LABELS`| `True` | `False` |

---

## 4. Verification Command Prior to Cutover

```bash
# Verify security configuration against production checklist
python manage.py check --deploy --settings=config.settings.production

# Verify migrations are fully synchronized
python manage.py makemigrations --check --settings=config.settings.production

# Run complete test suite
pytest
```
