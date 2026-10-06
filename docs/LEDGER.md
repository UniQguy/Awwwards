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
- **`apps.tax`**:
  - Services: `gst_calculator.py` (intra-state vs inter-state supply resolution, tax extraction and split), `line_allocator.py` (Hare-Niemeyer largest-remainder discount distribution in paise, gap-free cents invariant).
- **`apps.shipping`**:
  - `ShippingConfig` (singleton pk=1): `free_shipping_threshold`, `standard_fee`, `cod_fee`, `is_standard_fee_confirmed`.
  - `ShippingZone`: `name`, `pin_prefix`, `est_days_min`, `est_days_max`, `cod_allowed`, `is_active`.
  - `PincodeServiceability`: `pincode`, `est_days_min`, `est_days_max`, `cod_allowed`, `is_active`.
- **`apps.catalog`**:
  - `Category`: `name`, `slug`, `hsn_code`, `gst_rate`, `is_gst_rate_verified`, `accent_key`, `display_order`, `description`.
  - `Product`: `category`, `sku`, `slug`, `raw_name`, `display_name`, `source_asin`, `parsed_brand`, `selling_price`, `mrp`, `is_available`, `source_rating`, `source_rating_count`, `search_text`.
  - `ProductSpecification`: `product`, `key`, `value`, `source`, `is_highlight`, `display_order`.
  - `ProductMedia`: `product`, `media_type`, `external_image_url`, `local_image`, `alt_text`, `display_order`.
  - `Collection` & `FeaturedProduct`: Editorial collections with plinth slot assignments.
- **`apps.inventory`**:
  - `Inventory`: `product` (OneToOne), `quantity`, `low_stock_threshold`, `is_sample_data`.
  - `StockReservation`: `product`, `order` (FK lazy 'orders.Order'), `user`, `owner_key`, `quantity`, `status` (reserved/converted/released), `expires_at`, `extended_at`.
- **`apps.cart` & `apps.wishlist`**:
  - `Cart` & `CartItem`: Stock-clamped add/update, guest session support, subtotal, MRP savings, GST allocation.
  - `Wishlist` & `WishlistItem`: Product bookmarks, toggle, transfer to cart.
  - Login Merge: `apps/accounts/signals.py` merges guest cart/wishlist into user account on `user_logged_in`.
- **`apps.promotions`**:
  - `Coupon`: Case-insensitive `code`, `discount_type` (percentage/fixed), `discount_value`, `min_order_amount`, `max_discount_amount`, `applicable_categories`, limits, validity window.
  - `CouponRedemption`: Audit record of customer coupon redemptions.
- **`apps.orders`**:
  - `Order`: `order_number` (EC-YYYY-XXXX-XXXX), `user`, snapshots for shipping/billing addresses, financial snapshot (`subtotal`, `shipping_fee`, `discount_amount`, `tax_amount`, `total_amount`), `status`, `payment_method`, `payment_status`.
  - `OrderItem`: Line item snapshot with allocated GST taxes (`taxable_value`, `cgst_amount`, `sgst_amount`, `igst_amount`).
  - `OrderStatusHistory`: Lifecycle transition audit trail.
  - `InvoiceCounter`: Gap-free atomic sequential counters per financial year (`tax_invoice`, `bill_of_supply`, `credit_note`).
  - `Invoice`: Sequential gap-free invoice (`EC-INV-YYYY-YY-XXXXX` or `EC-BOS-YYYY-YY-XXXXX`).
  - `CreditNote`: Sequential gap-free GST credit note (`EC-CN-YYYY-YY-XXXXX`).
- **`apps.payments`**:
  - `PaymentTransaction`: Payment attempts, gateway IDs, status.
  - `WebhookEvent`: Inbound webhook audit and deduplication table.
- **`apps.search`**:
  - `execute_catalog_search`: Tokenized query matching, faceted filtering (categories, brands, price brackets), typo suggestions ("Did You Mean").

### 2. URLs & Endpoints
- `/health/` -> `health_check` (`name="health_check"`) -> Returns `{"status": "ok", "service": "electrocart"}`.
- `/admin/` -> `admin.site.urls` -> Django Administration interface.
- `/accounts/` -> `allauth.urls` -> Authentication, registration, password management.
- `/payments/razorpay/verify/` -> `razorpay_verify_view` -> POST signature verification and order confirmation.
- `/payments/razorpay/webhook/` -> `razorpay_webhook_view` -> POST asynchronous webhook event processing with replay protection.

### 3. Environment Variables
- `DEBUG`: Boolean (development: `True`, test/prod: `False`).
- `SECRET_KEY`: Django cryptographic signing secret.
- `DATABASE_URL`: Database connection string (`sqlite:///db.sqlite3` for local).
- `ALLOWED_HOSTS`: Comma-separated list of permitted host headers.
- `CSRF_TRUSTED_ORIGINS`: Comma-separated trusted origins for CSRF POST requests.
- `SELLER_STATE`: Indian State of seller origin (`Karnataka`), determines CGST+SGST vs IGST split.
- `SELLER_GSTIN`: Seller GST identification number (blank activates Bill of Supply mode).
- `RAZORPAY_KEY_ID`: Razorpay public key ID.
- `RAZORPAY_KEY_SECRET`: Razorpay secret key.
- `RAZORPAY_WEBHOOK_SECRET`: Razorpay webhook secret.
- `EMAIL_BACKEND`: `django.core.mail.backends.console.EmailBackend` for local development.

### 4. Core Business Rules
- **Tax Extraction**: All displayed catalog and checkout prices are strictly GST-inclusive. Tax extraction formula: `tax = price * rate / (100 + rate)`.
- **Bill of Supply**: If `SELLER_GSTIN` is omitted or empty, the application operates in Bill of Supply mode (no GST charged or displayed).
- **Precision Currency**: Money arithmetic is strictly performed in Python `Decimal` (`ROUND_HALF_UP`, 2 decimal places). SQL `Sum()` or `Avg()` over money fields is forbidden.
- **Sequential Invoicing**: Invoices and Credit Notes follow Indian financial year (April 1 - March 31) series (`EC-INV-YYYY-YY-XXXXX`, `EC-CN-YYYY-YY-XXXXX`) guaranteed gap-free via atomic database locks.
- **Stock Reservation**: 15-minute TTL holds during cart exploration, 30-minute holds during online gateway payment checkout. Released automatically on expiry or order cancellation.
- **Single Default Address**: Each customer can have at most one default address at any time, guaranteed at both model save and database constraint layers.
