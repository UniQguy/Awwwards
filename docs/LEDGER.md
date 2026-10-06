# ELECTROCART PROJECT LEDGER

### 1. Applications & Models
- **`apps.core`**:
  - `TimeStampedModel` (abstract): `created_at` (DateTimeField auto_now_add), `updated_at` (DateTimeField auto_now).
  - `UUIDModel` (abstract): `uuid` (UUIDField uuid4, unique, editable=False).
- **`apps.accounts`**:
  - `User`: `uuid`, `email` (EmailField unique, USERNAME_FIELD), `full_name`, `is_staff`, `is_active`, `created_at`, `updated_at`.
    - *Constraints*: `unique_user_email_lower` (`Lower("email")`).
    - *Manager*: `UserManager` (email normalization and lowercase enforcement).
  - `Address`: `uuid`, `user` (FK User), `full_name`, `phone`, `line1`, `line2`, `landmark`, `city`, `state` (36 IndianState choices), `pincode` (6-digit validator), `is_default`, `created_at`, `updated_at`.
    - *Constraints*: `unique_default_address_per_user` (`fields=["user"], condition=Q(is_default=True)`).
    - *Lifecycle*: `save()` atomically clears previous default address when `is_default=True`.

### 2. URLs & Endpoints
- `/health/` -> `health_check` (`name="health_check"`) -> Returns `{"status": "ok", "service": "electrocart"}`.
- `/admin/` -> `admin.site.urls` -> Django Administration interface.

### 3. Environment Variables
- `DEBUG`: Boolean (development: `True`, test/prod: `False`).
- `SECRET_KEY`: Django cryptographic signing secret.
- `DATABASE_URL`: Database connection string (`sqlite:///db.sqlite3` for local).
- `ALLOWED_HOSTS`: Comma-separated list of permitted host headers.
- `CSRF_TRUSTED_ORIGINS`: Comma-separated trusted origins for CSRF POST requests.
- `SELLER_STATE`: Indian State of seller origin (`Karnataka`), determines CGST+SGST vs IGST split.
- `SELLER_GSTIN`: Seller GST identification number (blank activates Bill of Supply mode).
- `RAZORPAY_KEY_ID`: Razorpay test key ID.
- `RAZORPAY_KEY_SECRET`: Razorpay test key secret.
- `EMAIL_BACKEND`: `django.core.mail.backends.console.EmailBackend` for local development.

### 4. Core Business Rules
- **Tax Extraction**: All displayed catalog and checkout prices are strictly GST-inclusive. Tax extraction formula: `tax = price * rate / (100 + rate)`.
- **Bill of Supply**: If `SELLER_GSTIN` is omitted or empty, the application operates in Bill of Supply mode (no GST charged or displayed).
- **Precision Currency**: Money arithmetic is performed in Python `Decimal` (`ROUND_HALF_UP`, 2 decimal places).
- **Single Default Address**: Each customer can have at most one default address at any time, guaranteed at both model save and database constraint layers.
- **Portability**: Database code must remain 100% portable between SQLite and PostgreSQL without Postgres-specific extensions.
