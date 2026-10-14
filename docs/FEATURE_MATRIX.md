# Comprehensive Feature Matrix & Traceability Matrix
**ELECTROCART Monograph Storefront**  
*Mapping of Academic & Engineering Requirements to Source Code and Automated Tests*

---

## 1. Editorial Storefront & Monograph Design System

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Monograph Aesthetic** | Restrained typography, Newsreader serif display, Inter body, warm monochromatic tonal palette with single amber accent | `frontend/css/tokens.css`<br>`frontend/css/typography.css`<br>`frontend/css/theme.css` | `tests/test_ui_standards.py`<br>`scripts/layout_audit.py` | **VERIFIED** |
| **Chapter Narrative** | Sequential chapter index with fixed side indicator (desktop) and mobile sticky indicator | `frontend/js/modules/chapter-nav.js`<br>`templates/catalog/home.html` | `scripts/full_qa.py`<br>`docs/ui-review/r4_visual_evidence/` | **VERIFIED** |
| **Hero Entrance** | Masked headline reveal, specular sheen on featured plates, graceful fallback on reduced motion | `frontend/js/modules/motion.js`<br>`frontend/css/motion.css` | `scripts/full_qa.py`<br>`tests/test_ui_standards.py` | **VERIFIED** |
| **Zero Visual Voiding** | Fluid typography clamping, constrained plate aspect ratios, no empty gaps on any screen | `frontend/css/tokens.css`<br>`frontend/css/components/product-card.css` | `scripts/fold_audit.py`<br>`scripts/void_audit.py` | **VERIFIED** |
| **Accessible Navigation** | WCAG 2.1 AA keyboard rings, skip links, aria-labels, 44px tap targets | `templates/base.html`<br>`templates/includes/header.html` | `scripts/layout_audit.py`<br>`docs/ACCESSIBILITY.md` | **VERIFIED** |

---

## 2. Product Catalog, Categorization & Search

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Faceted Filtering** | Multi-attribute filtering (brand, price range, in-stock status, rating) with clean URL query params | `apps/catalog/views.py`<br>`apps/catalog/services/filter_service.py` | `tests/test_catalog_filters.py`<br>`tests/test_views_catalog.py` | **VERIFIED** |
| **Category Marquee** | Editorial lead pick composition, structured listing grid, responsive columns | `templates/catalog/category_detail.html`<br>`apps/catalog/models.py` | `scripts/void_audit.py`<br>`docs/ui-review/commerce_features/` | **VERIFIED** |
| **Real Product Data** | 50 real consumer electronic hardware items imported from authentic Indian catalog data | `data/products_catalog.csv`<br>`apps/catalog/management/commands/import_products.py` | `tests/test_catalog_import.py`<br>`scripts/db_summary.py` | **VERIFIED** |
| **Full-Text Search** | SQLite/PostgreSQL full-text search across titles, specifications, and categories with rate limiting | `apps/search/views.py`<br>`apps/search/services/search_engine.py` | `tests/test_search.py`<br>`tests/test_flow_review.py` | **VERIFIED** |
| **Product Specifications** | Validated JSON hardware specs (audio drivers, connectivity, battery, display) | `apps/catalog/models.py`<br>`templates/catalog/product_detail.html` | `tests/test_catalog_models.py` | **VERIFIED** |

---

## 3. Product Detail Page (PDP) & Commerce Features

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sticky Purchase Column** | Dual-column responsive layout keeping price, inventory badge, and CTA sticky during scroll | `templates/catalog/product_detail.html`<br>`frontend/css/pages/pdp.css` | `scripts/fold_audit.py`<br>`docs/ui-review/fold_audit/` | **VERIFIED** |
| **Honest Rating System** | Star glyph rendering (`★★★★☆`) tied strictly to real Amazon India rating distributions | `apps/core/templatetags/core_tags.py`<br>`templates/catalog/product_detail.html` | `tests/test_templatetags.py`<br>`scripts/exercise_commerce_features.py` | **VERIFIED** |
| **Inline PIN Estimator** | Real-time PIN code delivery checker rendering speed tier, carrier zone, and estimated arrival | `apps/shipping/views.py`<br>`apps/shipping/services/estimator.py` | `tests/test_shipping.py`<br>`tests/test_flow_review.py` | **VERIFIED** |
| **Available Coupons** | Real-time display of currently applicable coupons on the product page | `apps/promotions/models.py`<br>`templates/catalog/product_detail.html` | `tests/test_promotions.py`<br>`scripts/exercise_commerce_features.py` | **VERIFIED** |
| **Privacy-First Recently Viewed** | Pure client-side `localStorage` tracking without cookies, server state, or telemetry | `frontend/js/modules/recently-viewed.js`<br>`templates/includes/recently_viewed_shelf.html` | `tests/test_views_catalog.py`<br>`scripts/exercise_commerce_features.py` | **VERIFIED** |

---

## 4. Shopping Bag & Two-Way Cart Preservation

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Cart Calculation** | Subtotal, discounts, statutory GST breakdown, and dynamic shipping calculations | `apps/cart/services/cart_calculator.py`<br>`apps/cart/models.py` | `tests/test_cart_calculator.py`<br>`tests/test_models_cart.py` | **VERIFIED** |
| **Two-Way Preservation** | Save for Later shelf preserving items and quantities with one-click restore to active bag | `apps/cart/models.py`<br>`apps/cart/views.py` | `tests/test_views_cart.py`<br>`scripts/exercise_commerce_features.py` | **VERIFIED** |
| **Free Shipping Bar** | Visual progress indicator toward free delivery threshold (e.g. orders over ₹1,000) | `templates/cart/cart_detail.html`<br>`apps/cart/services/cart_calculator.py` | `tests/test_views_cart.py` | **VERIFIED** |
| **Guest Cart Merging** | Seamless merging of anonymous cookie-based carts into authenticated user accounts upon login | `apps/cart/services/cart_service.py`<br>`apps/accounts/signals.py` | `tests/test_cart_service.py` | **VERIFIED** |

---

## 5. Promotions & Coupon Engine

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Coupon Validation** | Enforces minimum spend, expiration dates, usage limits, and single-coupon session rules | `apps/promotions/services/coupon_validator.py`<br>`apps/promotions/models.py` | `tests/test_promotions.py`<br>`tests/test_flow_review.py` | **VERIFIED** |
| **Anti-Stacking Rules** | Strict prohibition against multiple coupon codes stacking on a single order | `apps/cart/views.py`<br>`apps/cart/services/cart_service.py` | `tests/test_flow_review.py` | **VERIFIED** |
| **Usage Tracking** | Global usage counter and per-user usage limits incremented atomically upon order placement | `apps/promotions/models.py`<br>`apps/orders/services/order_creator.py` | `tests/test_promotions.py`<br>`tests/test_flow_review.py` | **VERIFIED** |

---

## 6. Shipping & Delivery Logistics

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Indian PIN Code Engine**| 6-digit regex validation, region mapping (Metro, Regional, Rest of India), and transit days | `apps/shipping/services/estimator.py`<br>`apps/shipping/models.py` | `tests/test_shipping.py`<br>`tests/test_flow_review.py` | **VERIFIED** |
| **Rate Limiting** | Protection against PIN code enumeration via strict HTTP 429 throttling | `apps/shipping/views.py` | `tests/test_flow_review.py` | **VERIFIED** |
| **Zone Management** | Admin-manageable shipping zones, flat-rate tiers, and free delivery thresholds | `apps/shipping/models.py`<br>`apps/shipping/admin.py` | `tests/test_admin_security.py` | **VERIFIED** |

---

## 7. Checkout Flow & Guest Checkout

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Guest Checkout** | Clean guest path without forced registration; stores guest email and phone in session | `apps/orders/views.py`<br>`templates/orders/checkout_start.html` | `tests/test_views_orders.py`<br>`scripts/offline_check.py` | **VERIFIED** |
| **Address Capture** | Indian postal address form with state dropdown, PIN code validation, and landmark field | `apps/accounts/models.py`<br>`templates/orders/checkout_address.html` | `tests/test_views_orders.py` | **VERIFIED** |
| **Price Tampering Defense**| Server re-evaluates all prices and amounts from live DB records; client payload amounts ignored | `apps/orders/services/order_creator.py` | `tests/test_flow_review.py` | **VERIFIED** |
| **Atomic Deduplication** | Double-submit protection clears cart atomically; prevents duplicate orders or double charges | `apps/orders/services/order_creator.py` | `tests/test_flow_review.py` | **VERIFIED** |

---

## 8. Order Lifecycle & Statutory Invoicing

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Order Numbering** | High-entropy sequential identifiers (e.g. `EC-20261014-XXXX`) avoiding IDOR enumeration | `apps/orders/models.py`<br>`apps/orders/services/order_creator.py` | `tests/test_flow_review.py`<br>`tests/test_models_orders.py` | **VERIFIED** |
| **Order State Machine** | Strict valid state transitions (`PENDING` -> `CONFIRMED` -> `SHIPPED` -> `DELIVERED` / `CANCELLED`) | `apps/orders/services/order_status.py` | `tests/test_order_status.py`<br>`tests/test_admin_security.py` | **VERIFIED** |
| **Statutory Tax Invoice**| Section 31 CGST Act PDF invoice with HSN table, CGST/SGST/IGST, and words INR | `apps/orders/services/invoicing.py`<br>`apps/orders/services/invoice_pdf.py` | `tests/test_invoices.py` | **VERIFIED** |
| **GST Credit Notes** | Statutory Section 34 CGST Act credit note PDFs issued upon order cancellation or return | `apps/orders/services/invoicing.py`<br>`apps/orders/services/invoice_pdf.py` | `tests/test_invoices.py` | **VERIFIED** |

---

## 9. Payments & Webhooks

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Multi-Payment Support** | Cash on Delivery (COD) and Razorpay mock/live integration (UPI, Cards, Netbanking) | `apps/payments/views.py`<br>`apps/payments/services/razorpay_client.py` | `tests/test_payments.py` | **VERIFIED** |
| **Webhook Signature Verification** | HMAC SHA-256 cryptographic signature validation on incoming payment webhooks | `apps/payments/views.py`<br>`apps/payments/services/webhook_service.py` | `tests/test_flow_review.py` | **VERIFIED** |
| **Idempotent Webhooks** | Duplicate webhook replay deduplication prevents double processing of payment events | `apps/payments/views.py` | `tests/test_flow_review.py` | **VERIFIED** |

---

## 10. Operations & Admin Console

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Store Operations Dashboard** | Admin index snapshot: orders today, Python Decimal revenue, status breakdown, low-stock count | `config/urls.py`<br>`templates/admin/index.html` | `tests/test_admin_security.py`<br>`docs/ui-review/admin_e2e/` | **VERIFIED** |
| **CSV Order Export** | Staff-only admin bulk export action generating detailed CSV files of orders | `apps/orders/admin.py` | `tests/test_admin_security.py` | **VERIFIED** |
| **Role-Based Access Control**| Granular permission groups (`Store manager`, `Demo Staff`) restricting access to financials | `apps/accounts/management/commands/create_demo_admin.py` | `tests/test_admin_security.py` | **VERIFIED** |
| **Inventory Monitoring** | Low-stock filtering (`quantity <= low_stock_threshold`) and atomic stock decrements | `apps/inventory/admin.py`<br>`apps/inventory/services/reservation_service.py` | `tests/test_admin_security.py`<br>`tests/test_flow_review.py` | **VERIFIED** |

---

## 11. Transactional Email & Dev Outbox

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Configurable Email Modes**| Environment-driven `EMAIL_MODE` (`file`, `console`, `smtp`) for zero-dependency local testing | `config/settings/base.py`<br>`apps/core/email_backends.py` | `tests/test_email_delivery.py`<br>`docs/EMAIL_SETUP.md` | **VERIFIED** |
| **MIME Outbox Inspector**| `/dev/outbox/` web UI parsing RFC 5322 `.eml` files in `.emails/` with raw headers and HTML preview | `apps/core/views_outbox.py`<br>`templates/core/dev_outbox.html` | `docs/ui-review/auth_e2e/`<br>`tests/test_email_delivery.py` | **VERIFIED** |
| **Transactional Triggers**| Automated emails on order confirmation, COD placement, shipment, and refunds | `apps/orders/services/email_notifier.py` | `tests/test_views_orders.py` | **VERIFIED** |

---

## 12. Security, Compliance & System Rigor

| Requirement | Implementation Architecture | Primary Source Files | Verification & Automated Tests | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Atomic Stock Locking & Reservations** | Atomic conditional `UPDATE` and inventory reservations preventing oversell race conditions | `apps/inventory/services/reservation_service.py` | `tests/test_flow_review.py` | **VERIFIED** |
| **CSRF Defense** | Strict CSRF token validation on all state-modifying POST requests; 403 on missing token | `django.middleware.csrf.CsrfViewMiddleware` | `tests/test_flow_review.py` | **VERIFIED** |
| **Rate Limiting** | IP-based rate limiting on sensitive checkout, search, and coupon endpoints | `django_ratelimit.decorators.ratelimit` | `tests/test_flow_review.py` | **VERIFIED** |
| **Zero External CDN Dependencies** | Fully offline-operable frontend with local fonts, local media caching, and SVG fallbacks | `scripts/offline_check.py`<br>`frontend/css/fonts.css` | `scripts/offline_check.py` | **VERIFIED** |
| **Academic Demonstration Notices** | Prominent disclaimers across all legal pages, invoices, and checkout flows | `templates/pages/legal_*.html`<br>`templates/orders/order_invoice.html` | `tests/test_contact.py`<br>`scripts/offline_check.py` | **VERIFIED** |
