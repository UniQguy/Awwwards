# Security Review & Threat Model Analysis

This document details the security posture, business-logic threat mitigations, dependency audits, secrets audits, and access controls implemented for **ELECTROCART**.

---

## 1. Business Logic Invariants & Mitigations

| Threat Vector | Mitigation Strategy | Enforcing Module | Verification Test |
| :--- | :--- | :--- | :--- |
| **Price Tampering** | Unit and line prices are strictly read from `Product.selling_price` in the database at the instant of order placement. Client requests cannot supply prices or override discounts. | `apps.orders.services.order_creator` | `tests.test_security_hardening.SecurityHardeningTests.test_price_tampering_impossible` |
| **Stock Overselling & Race Conditions** | High-concurrency TTL inventory reservations (`StockReservation`) with atomic database transactions (`select_for_update` / atomic increments). Zero-stock products cannot be placed into bag or checked out. | `apps.inventory.services.reservation_service` | `tests.test_security_hardening.SecurityHardeningTests.test_stock_overselling_prevented` |
| **Coupon Code Brute-Force & Replay** | Strict rate limits (10 attempts/min per IP) on coupon application. Coupons enforce expiration dates, usage limits (`usage_limit`), per-user uniqueness (`CouponUsage`), and minimum subtotal thresholds. | `apps.promotions.services.coupon_validator`, `apps.cart.views` | `tests.test_security_hardening.SecurityHardeningTests.test_rate_limit_coupon_apply_returns_429` |
| **Guest-Order & IDOR Enumeration** | Sequential order numbers (`EC-YYYYMMDD-XXXX`) cannot be browsed anonymously. Access to order confirmation, invoice, and tracking requires either user authentication matching `order.user` or a cryptographically signed/session-bound token (`?token=`). Non-matching access returns HTTP 404. | `apps.orders.views._validate_order_access` | `tests.test_security_hardening.SecurityHardeningTests.test_idor_protection_on_orders` |
| **Webhook Replay & Spoofing** | Inbound Razorpay webhooks require valid HMAC-SHA256 signatures (`X-Razorpay-Signature`) verified against `RAZORPAY_WEBHOOK_SECRET`. Processed events check idempotency and database state before performing mutations. | `apps.payments.services.webhook_processor` | `tests.test_payments.RazorpayWebhookTests.test_webhook_valid_signature` |
| **CSRF on Mutations** | Django CSRF protection is active across all state-mutating HTTP methods (`POST`, `PUT`, `DELETE`). Only the signature-verified Razorpay webhook endpoint is exempt. | `django.middleware.csrf.CsrfViewMiddleware` | `tests.test_security_hardening.SecurityHardeningTests.test_csrf_protection_on_mutations` |
| **Malicious File Uploads** | `ProductMedia.local_image` enforces a 5MB size cap, pillow byte inspection verifying valid image structures (`JPEG`, `PNG`, `WEBP`, `AVIF`), and sanitized UUID-based filenames to prevent path traversal or script execution. | `apps.catalog.models.validate_product_image_upload` | `tests.test_security_hardening.SecurityHardeningTests.test_upload_validation_rejects_non_image` |

---

## 2. Abuse Prevention & Rate Limiting

The application implements IP and user-keyed rate limits via `django-ratelimit` and `allauth.core.ratelimit`:

| Endpoint / Action | Rate Limit | Behavior on Limit |
| :--- | :--- | :--- |
| `POST /cart/coupon/apply/` | 10 / minute / IP | HTTP 429 Too Many Requests (`templates/429.html`) |
| `GET /search/suggest/` | 60 / minute / IP | HTTP 429 JSON (`{"error": "Rate limit exceeded."}`) |
| `POST /orders/track/` | 15 / minute / IP | HTTP 429 Too Many Requests |
| `POST /shipping/check/` | 20 / minute / IP | HTTP 429 Too Many Requests |
| `POST /checkout/place/` | 10 / minute / IP | HTTP 429 Too Many Requests |
| `POST /payments/razorpay/webhook/` | 120 / minute / IP | HTTP 429 JSON |
| Authentication: Login | 30 / minute / IP | Allauth HTTP 429 |
| Authentication: Signup | 20 / minute / IP | Allauth HTTP 429 |
| Authentication: Password Reset | 20 / minute / IP | Allauth HTTP 429 |

---

## 3. Logging Security & Redaction

The logging pipeline utilizes `apps.core.logging_filters.SensitiveDataFilter` to prevent leaks into server logs or log aggregators:
- **Guest Access Tokens**: `?token=...` is replaced with `?token=[REDACTED]`
- **Signature Parameters**: `?sig=...` is replaced with `?sig=[REDACTED]`
- **Customer Email Addresses**: Partially masked to preserve debugging visibility while protecting PII (e.g., `alice@example.com` becomes `al***@example.com`).
- **Payment Keys**: Razorpay keys (`rzp_test_...` or `rzp_live_...`) are truncated after the prefix.

Verified via `tests.test_security_hardening.SecurityHardeningTests.test_logging_redaction_filter`.

---

## 4. HTTP Security Headers

Every storefront and administrative response includes modern defensive headers:
- `Content-Security-Policy`:
  - `default-src 'self'`
  - `script-src 'self' https://checkout.razorpay.com`
  - `frame-src 'self' https://api.razorpay.com`
  - `object-src 'none'`
  - `frame-ancestors 'none'`
- `Permissions-Policy`: `camera=(), microphone=(), geolocation=(), payment=(self "https://checkout.razorpay.com")`
- `Cross-Origin-Opener-Policy`: `same-origin`
- `Referrer-Policy`: `strict-origin-when-cross-origin` (overridden to `no-referrer` on sensitive checkout/account/order pages)
- `X-Frame-Options`: `DENY`
- `X-Content-Type-Options`: `nosniff`

---

## 5. Dependency Audit Findings

### Python Dependencies (`pip-audit`)
- `Pillow`: Upgraded to `>=11.0,<13.0` (12.3.0 installed). Clean.
- `python-dotenv`: Upgraded to `>=1.1,<1.3` (1.2.4 installed). Clean.
- `setuptools`: Pinned to `>=75.0,<76.0` (75.8.0 installed).
  - *Finding*: `pip-audit` notes advisory on setuptools $<83.0.0$.
  - *Accepted Vendor Rationale*: Upstream official Razorpay Python SDK (`razorpay==1.4.1`) requires `pkg_resources` at runtime (`from razorpay.client import Client -> import pkg_resources`). Setuptools 83+ removes `pkg_resources`. This is a known, accepted constraint until Razorpay publishes a modernized SDK.

### Node Dependencies (`npm audit`)
- Audit identified devDependency advisories in `vite` (5.4.14) and `vitest` (2.1.8).
- *Status*: Accepted build-time toolchain constraint. Neither Vite nor Vitest is present in production environments, run on live servers, or served to clients. Client assets are pre-compiled and immutable.

---

## 6. Secrets & Credentials Scan

A comprehensive regex audit was executed across the entire repository history (`git log -p --all`):
- `DATABASE_URL`: 0 matches in git history.
- `SECRET_KEY`: Exactly 2 matches in git history corresponding to the initial scaffolding commit placeholder (`django-insecure-6ewnr...`). The active environment requires an explicit `SECRET_KEY` in `.env`.
- `RAZORPAY_KEY`: 0 real keys found. All matches in history are safe mock identifiers (`rzp_test_placeholder`, `rzp_test_mock`).
