# Phase 8A Engineering & Truth Report: Fix Pass 1 (Correctness, Data Truth, Flow)

**Date:** October 8, 2026  
**Auditor/Engineer:** DeepMind Antigravity Pair  
**Scope:** Pass 1: S0 Correctness and Data Truth Fixes (F-01 through F-06), F-07 (search suggestions behavior), F-11 (display name cleanup), F-12 (near-duplicate picks elimination), and F-25 (unseen flows and pages audit).

---

## Executive Summary

Fix Pass 1 targeted structural correctness, catalog truth, transaction integrity, and purchase flow reliability. All targeted findings have been systematically resolved with concrete automated verification and real-browser Playwright execution.

1. **F-01 (Guest Checkout 403)**: **CLOSED**. Root cause identified as `Referrer-Policy: no-referrer` stripping Origin headers on HTTP form posts + unhandled GET requests to `/checkout/guest/` + CSRF trusted origin configuration. Fixed via `Referrer-Policy: same-origin`, GET redirect to checkout flow start, customized human-friendly CSRF error screen, and trusted origin alignment.
2. **F-02 (Category Classification)**: **CLOSED**. Implemented deterministic scoring and priority disambiguation engine (`apps/catalog/services/category_rules.py`). Reclassified all 7,149 products in the live catalog. Zero Redmi phones in cameras, zero SanDisk SD cards in cameras, zero Fire TV Sticks in TVs.
3. **F-03 (Wrong Specs / Unit Misattribution)**: **CLOSED**. Rebuilt technical spec parser (`apps/catalog/services/spec_extractor.py`) with explicit inch precedence over centimetre dimensions, centimetre-to-inch metric fallback, strict category sanity bounds, and storage vs. RAM disambiguation.
4. **F-04 / Honesty Sweep (F-16, F-17, F-18, F-22, F-23)**: **CLOSED**. Removed all fabricated marketing claims, buzzwords, and architectural hype across catalog descriptions, home copy, categories index, and footer. Implemented automated gatekeeper test `scripts/audit_copy_honesty.py` and `tests/test_copy_honesty.py` (10/10 PASS).
5. **F-05 & F-06 (Tax Mode Contradiction & Cart Footing)**: **CLOSED**. Unified tax architecture to support both Regular GST Dealer (`gst`) and Bill of Supply (`bill_of_supply`) modes with complete consistency across footer, cart, checkout, and invoices. Fixed cart arithmetic so every displayed line is mathematically reconciled, with MRP savings presented strictly as an informational callout outside the subtotal summation.
6. **F-07 (Search Suggestions Behavior)**: **CLOSED (Behavioral)**. Built real-time asynchronous suggestions endpoint (`/search/suggest/`), WAI-ARIA 1.2 Combobox markup, 150ms debounced client controller with keyboard navigation (ArrowDown/ArrowUp, Enter, Escape) and click-away closing.
7. **F-11 (`display_name`) & F-12 (Near-Duplicate Picks)**: **CLOSED**. Implemented `clean_display_name` (enforcing max 90 characters, punctuation balancing, connector stripping) and `family_key` normalization grouping color/size variants to guarantee diverse editorial shelves.
8. **F-25 (Unseen Pages & Flows Sweep)**: **VERIFIED**. Full purchase lifecycle (Cart -> Guest Info -> Address -> Review -> COD Place Order -> Tracking -> Invoice -> Order Cancellation) executed and verified in real browser alongside responsive sweeps (1456px desktop, 390px mobile) across 15 utility, legal, and error views.

---

## 1. Finding Status Register

| Finding ID | Severity | Description | Pass 1 Status | Verification Artifact |
|---|---|---|---|---|
| **F-01** | S0 | Guest checkout 403 Forbidden | **CLOSED** | `scripts/e2e_browser.py`, `tests/test_views_checkout.py` |
| **F-02** | S0 | Wrong categories (Phones/SD cards in Cameras, Fire TV in TVs) | **CLOSED** | `reports/reclassification.md`, `tests/test_category_rules.py` |
| **F-03** | S0 | Wrong specs (cm misread as inches, out-of-bound display sizes) | **CLOSED** | `reports/specs_distribution.md`, `tests/test_spec_extractor.py` |
| **F-04** | S0 | Invented marketing copy & exaggerated claims | **CLOSED** | `scripts/audit_copy_honesty.py`, `tests/test_copy_honesty.py` |
| **F-05** | S0 | Tax mode contradiction (Bill of Supply vs GST breakdown) | **CLOSED** | `tests/test_tax_mode_and_footing.py` |
| **F-06** | S0 | Cart arithmetic does not foot (MRP savings appearing in math) | **CLOSED** | `tests/test_tax_mode_and_footing.py` |
| **F-07** | S1 | Search suggestions panel missing / non-functional (Behavior) | **CLOSED (Behavior)** | `tests/js/search_suggest.test.js`, Playwright tests |
| **F-11** | S1 | Display name truncation & punctuation collision (Part: display_name) | **CLOSED** | `tests/test_families_and_display_names.py` |
| **F-12** | S1 | Editorial chapter picks are near-duplicate color/storage variants | **CLOSED** | `tests/test_families_and_display_names.py` |
| **F-25** | S2 | Audit unseen pages and flows (legal, account, errors, checkout) | **VERIFIED** | `docs/ui-review/pass1_unseen.md`, `reports/e2e/` |

---

## 2. WP0 & Real-Browser Harness Verification

A production-grade Playwright Chromium harness was created in `scripts/e2e_browser.py`. It starts the Django ASGI/WSGI server locally on a clean port, binds a headless Chromium browser instance (`153.0.8010.12`), exercises live interactions, captures console errors and failed HTTP requests, and saves full-page screenshots to `reports/e2e/`.

### Browser Verification Summary
- **Browser**: Chromium 153.0.8010.12 (Headless)
- **Viewports Tested**: Desktop (1456 × 900 px), Mobile (390 × 844 px)
- **Total Screenshots Captured**: 47 image artifacts
- **JavaScript Console Errors Detected During End-to-End Flow**: 0
- **HTTP 5xx Server Errors Encountered**: 0

### Key Captured Screenshots:
- `f01_cart.png`: Cart state before initiating checkout.
- `f01_checkout_landed.png`: `/checkout/` entry page rendered with 200 OK.
- `f01_127_after_guest_submit.png`: Guest details successfully accepted on `http://127.0.0.1:8000`.
- `f01_localhost_after_guest_submit.png`: Guest details successfully accepted on `http://localhost:8000`.
- `full_flow_01_cart.png` to `full_flow_08_order_cancelled.png`: Complete purchase flow from cart through address, review, COD order placement (`EC-2026-59WS-Z3T5`), live tracking timeline, HTML invoice preview, and final customer cancellation.
- `search_suggest_01_open.png` to `search_suggest_04_rapid.png`: Live combobox suggestions rendering categories, brands, and products.

---

## 3. WP1: Root Cause & Resolution for F-01 (Checkout 403)

### Diagnostic Analysis
1. **Referrer Header Stripping**: `SensitivePageHeadersMiddleware` formerly emitted `Referrer-Policy: no-referrer`. Under Django 5 CSRF protection, HTTP POST submissions across origin variants require an origin or referrer header matching `CSRF_TRUSTED_ORIGINS`.
2. **Direct GET to `/checkout/guest/`**: Shoppers navigating directly to `/checkout/guest/` or refreshing the guest stage triggered an HTTP 405 / 403 PermissionDenied instead of being gracefully routed back into the flow.
3. **CSRF Origins**: `CSRF_TRUSTED_ORIGINS` in local development required explicit coverage for both `http://127.0.0.1:8000` and `http://localhost:8000`.

### Applied Fixes
1. Updated `SensitivePageHeadersMiddleware` to send `Referrer-Policy: same-origin`, preserving origin headers for internal form submissions while protecting external leaks.
2. In `apps/orders/views.py:checkout_guest`, implemented graceful redirection: GET requests automatically redirect to `orders:checkout_start`.
3. Created `templates/403_csrf.html` with honest, calm copy: *"That didn't go through. Your session may have expired. Reload the page and try again."*
4. Verified end-to-end checkout on both loopback hosts:
   - `http://127.0.0.1:8000`: HTTP 302 Redirect to Address step. (PASS)
   - `http://localhost:8000`: HTTP 302 Redirect to Address step. (PASS)

---

## 4. WP2: Catalog Reclassification (F-02)

To permanently resolve category contamination, `apps/catalog/services/category_rules.py` was established with domain-specific negative filters and precedence gates:
- **Exclusion Filters**:
  - Memory cards and card readers (SanDisk, MicroSD, SDXC, UHS-I) are hard-routed away from `cameras` to `other` (sundry storage).
  - Streaming media players (Fire TV Stick, Chromecast, TV boxes) and remotes are hard-routed away from `tvs` to `other`.
  - Camera bags, tripods, straps, and lens caps are excluded from `cameras`.
- **Precedence Hierarchy**:
  1. Negative hard exclusions
  2. Cases, straps, and screen protectors (including watch straps)
  3. Cables, chargers, and power banks
  4. Televisions and monitors (Redmi TVs are matched before phone rules)
  5. Audio: Earphones/Headphones vs Speakers
  6. Smartwatches & Wearables
  7. Keyboards & Mice
  8. Cameras & Optical devices
  9. Smartphones & Cellular devices

### Database Reclassification Summary (`reports/reclassification.md`)
- **Total Catalog Products Evaluated**: 7,149
- **Total Products Updated in Database**: 29
- **Zero-Tolerance Criteria**:
  - Cameras containing "Redmi": **0** (Target: 0)
  - Cameras containing "SanDisk": **0** (Target: 0)
  - Cameras containing "SD Card": **0** (Target: 0)
  - Displays & Televisions containing "Fire TV Stick": **0** (Target: 0)

### Current Category Breakdown
| Category Slug | Name | SKUs | Catalog Share |
|---|---|---|---|
| `cases-protectors` | Cases & Protectors | 770 | 10.8% |
| `earphones-headphones` | Earphones & Headphones | 703 | 9.8% |
| `cables-chargers-powerbanks` | Cables, Chargers & Power | 447 | 6.3% |
| `smartphones` | Smartphones & Devices | 422 | 5.9% |
| `keyboards-mice` | Keyboards & Pointers | 318 | 4.4% |
| `smartwatches-bands` | Smartwatches & Wearables | 289 | 4.0% |
| `speakers` | Acoustics & Speakers | 169 | 2.4% |
| `tvs` | Displays & Televisions | 124 | 1.7% |
| `cameras` | Cameras & Optics | 99 | 1.4% |
| `other` | Sundry Electronics | 3,808 | 53.3% |

---

## 5. WP3: Specification Parser & Sanity Bounds (F-03)

### Core Algorithmic Changes (`apps/catalog/services/spec_extractor.py`)
1. **Explicit Inch Priority**: When a title contains both centimetre and inch designations (e.g., *"Redmi 80 cm (32 inches) Android Smart TV"*), the parser strictly captures the inch match (`32"`).
2. **Metric Conversion Fallback**: If only centimetres are specified, value is converted using $cm / 2.54$ with integer or single-decimal formatting.
3. **Category Boundary Guards (`SANITY_RANGES`)**:
   - `tvs`: 15.0" to 120.0"
   - `smartphones`: 3.0" to 8.0"
   - `smartwatches-bands`: 0.9" to 2.5"
   - Out-of-bounds numbers are discarded and logged, preventing misattributed dimensions (e.g. 4.29cm smartwatches showing as 4.29").
4. **RAM vs. Storage Disambiguation**:
   - Expressions like `"6GB + 128GB"` or `"6GB / 128GB"` map $6\text{ GB} \to \text{RAM}$ and $128\text{ GB} \to \text{Storage}$.

### Specification Distribution Matrix (`reports/specs_distribution.md`)
- **Total Validated Specifications Generated**: 7,117

| Category | Specification Key | Minimum | Median | Maximum | Sample Size |
|---|---|---|---|---|---|
| `smartphones` | `screen_size` | 5.45" | 6.47" | 8.0" | 16 SKUs |
| `smartphones` | `ram` | 2 GB | 6 GB | 16 GB | 246 SKUs |
| `smartphones` | `storage` | 32 GB | 128 GB | 512 GB | 226 SKUs |
| `smartphones` | `battery` | 5000 mAh | 5000 mAh | 8200 mAh | 55 SKUs |
| `smartwatches-bands` | `screen_size` | 1.28" | 1.695" | 1.99" | 112 SKUs |
| `tvs` | `screen_size` | 17" | 40" | 80" | 109 SKUs |
| `cables-chargers-powerbanks` | `battery` | 1000 mAh | 10000 mAh | 50000 mAh | 68 SKUs |
| `earphones-headphones` | `playtime` | 4 Hours | 32 Hours | 120 Hours | 280 SKUs |

---

## 6. WP4: Honesty Sweep

Every fabricated marketing phrase identified in `docs/UI_FINDINGS.md` was removed from templates and database models:
- **Category Descriptions**: All category descriptions in the database were cleared to `""`.
- **Home Copy**:
  - Headline: *"Seven thousand items of personal and home electronics, indexed directly from Indian retail data with verified tax calculations and delivery estimates."*
  - Subline: *"A demonstration shop built on real product data. Filter by price, search across categories, and track sample orders end-to-end."*
  - Sections: *"The categories"*, *"How buying works"*, *"The brands"*.
  - Closing line: *"Start with the category you need."* (Removed *"precision electronics and honest craft"*).
- **Categories Index (`/c/`)**:
  - Title: *"All categories"*
  - Subhead: *"10 categories across 7,149 products. Prices from ₹39 to ₹1,49,990."*
- **Footer**:
  - Replaced promotional copy with: *"ElectroCart. A demonstration electronics store built with Django and modern web standards."*
  - Replaced ambiguous tax claim with unified Seller Tax Mode notice.
  - Removed engineering buzzwords from customer footer.
- **Razorpay Interface**:
  - Button text: *"Pay ₹{{ order.grand_total }} with Razorpay"* (Removed *"Payment Authorization"*).
  - Terms notice: *"Subject to standard returns policy."* (Removed *"within statutory limits"*).

### Automated Honesty Verification
`scripts/audit_copy_honesty.py` and `tests/test_copy_honesty.py` scanned 73 template files for banned vocabulary (`"precision electronics"`, `"honest craft"`, `"architectural"`, `"calibrated materials"`, `"acoustic instruments"`, `"pocket communicators"`, `"cinema prime"`, `"OLED cinema"`, `"Dolby Atmos"`, etc.):
- Result: **0 violations detected. 10/10 PASS.**

---

## 7. WP5: Tax Mode & Cart Footing (F-05, F-06)

### Unified Tax Architecture
The shop is configured as a **Regular GST Dealer** (`settings.SELLER_TAX_MODE = "gst"`):
- **Footer**: Displays Demo GSTIN (`29AABCU9603R1ZM`) and indicates prices are inclusive of applicable GST.
- **Cart & Review**: Displays informational note *"Includes GST of ₹X (18%)"*.
- **Invoices**: Formatted as **TAX INVOICE** with CGST/SGST/IGST and HSN columns.
- **Bill of Supply Toggle**: When `SELLER_TAX_MODE = "bill_of_supply"`, all GST callouts, calculations, and invoice headers switch cleanly to Bill of Supply rules with zero GST references.

### Cart Footing Mathematics
Cart arithmetic was restructured so the totals calculate without ambiguity:
$$\text{Grand Total} = \text{Items Subtotal} - \text{Coupon Discount} + \text{Delivery Fee} + \text{COD Fee}$$
- **Retail Savings (MRP)**: Rendered outside the arithmetic block as an informational callout:
  *"You save ₹X (Y%) compared with the listed MRP."*
- Verified through `tests/test_tax_mode_and_footing.py` (7/7 PASS).

---

## 8. WP6: Product Families (F-12) & Display Names (F-11)

1. **Family Key Normalization (`apps/catalog/services/families.py`)**:
   - Generates normalized keys by stripping color variants, storage capacities, RAM specifications, and pack sizes from titles.
   - Used to deduplicate editorial chapter plates and carousel picks, ensuring that users see distinct models rather than multiple color SKUs of boAt Bassheads or Redmi 9A.
2. **Display Name Sanitation (`apps/catalog/services/parsing.py`)**:
   - `clean_display_name()` enforces a maximum length of 90 characters, eliminates mid-phrase truncation, strips trailing separators (`-`, `|`, `,`), balances parentheses/quotes, and cleans redundant brand prefixes.
   - Tested across real catalog strings in `tests/test_families_and_display_names.py` (7/7 PASS).

---

## 9. WP7: Search Suggestions Behavior (F-07)

- **Backend (`/search/suggest/`)**:
  - Implemented in `apps/search/views.py`.
  - Returns structured JSON: up to 2 matching categories, up to 3 matching brands, and up to 5 matching products, with a final "See all results for '...'" link.
- **Frontend Combobox (`frontend/js/modules/search-suggest.js`)**:
  - WAI-ARIA 1.2 Combobox specification (`role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`, `aria-activedescendant`).
  - 150ms debounce with `AbortController` cancellation for superseded network requests.
  - Full keyboard accessibility: ArrowDown, ArrowUp, Enter to activate, Escape to close.
  - Click-away backdrop listener.
- **Testing**:
  - Unit tests: `tests/js/search_suggest.test.js` (3/3 PASS).
  - Real browser Playwright tests in `scripts/e2e_browser.py` verified slow typing, rapid keystrokes, ArrowDown navigation, Enter navigation, and mouse selection.

---

## 10. WP8: Unseen Pages Sweep (F-25)

The complete inventory of pages was audited under real browser viewports (1456px Desktop, 390px Mobile). Details are registered in `docs/ui-review/pass1_unseen.md`.

| Page Type | Desktop (1456px) | Mobile (390px) | Layout & Styling Status |
|---|---|---|---|
| `/about/` | 200 OK | 200 OK | Warm paper background, single column, editorial layout |
| `/legal/terms/` | 200 OK | 200 OK | Compliant legal copy, readable line-length |
| `/legal/refunds/` | 200 OK | 200 OK | Accurate returns policy, clean typography |
| `/legal/shipping/` | 200 OK | 200 OK | Verified delivery timeframes, pin code guidance |
| `/legal/privacy/` | 200 OK | 200 OK | Zero third-party trackers, privacy policy intact |
| `/categories/` | 200 OK | 200 OK | 10 canonical categories, correct product counts |
| `/brands/` | 200 OK | 200 OK | Alphabetical brand directory, clean link targets |
| `/cart/` (empty) | 200 OK | 200 OK | Calm empty state, "Return to shop" callout |
| `/accounts/login/` | 200 OK | 200 OK | Standard auth form, warm background |
| `/accounts/signup/` | 200 OK | 200 OK | Clean user registration |
| 404 Not Found | 404 OK | 404 OK | Direct explanation, link back to catalogue |
| 403 Forbidden | 403 OK | 403 OK | Dignified message, no cryptic errors |
| 403 CSRF Expired | 403 OK | 403 OK | Helpful explanation and reload button |
| 429 Rate Limit | 429 OK | 429 OK | Rate limiting notice with retry guidance |
| 500 Server Error | 500 OK | 500 OK | Calm error page without trace leaks |

---

## 11. Verification Matrix & Test Counts

| Test Suite | Tests Executed | Passed | Failed | Errors |
|---|---|---|---|---|
| **Python Test Suite (`manage.py test`)** | 261 | 261 | 0 | 0 |
| **JavaScript Test Suite (`npm run test:js`)** | 52 | 52 | 0 | 0 |
| **Copy & Honesty Audit (`scripts/audit_copy_honesty.py`)** | 73 files scanned | 10/10 PASS | 0 | 0 |
| **Classification Integrity Audit (`scripts/classification_audit.py`)** | 7,149 SKUs | PASS | 0 | 0 |
| **Vite Production Asset Build (`npm run build`)** | 34 modules | Built in 2.43s | 0 | 0 |
| **Django System Checks (`manage.py check`)** | Core check | 0 issues | 0 | 0 |
| **Django Migrations (`makemigrations --check`)** | Migration sync | 0 changes | 0 | 0 |
| **End-to-End Playwright Browser Harness** | Full purchase flow | Verified | 0 | 0 |

---

## 12. Git Status

```text
On branch main
Your branch is ahead of 'origin/main' by 33 commits.
  (use "git push" to publish your local commits - NEVER RUN AS PER STANDING ORDERS)

Changes to be committed / untracked files:
  apps/cart/services/cart_calculator.py
  apps/catalog/admin.py
  apps/catalog/models.py
  apps/catalog/services/category_rules.py
  apps/catalog/services/editorial.py
  apps/catalog/services/families.py
  apps/catalog/services/parsing.py
  apps/catalog/services/spec_extractor.py
  apps/catalog/views.py
  apps/catalog/management/commands/rebuild_display_names.py
  apps/catalog/management/commands/rebuild_specs.py
  apps/catalog/management/commands/reclassify_products.py
  apps/core/context_processors.py
  apps/core/middleware.py
  apps/core/views.py
  apps/orders/views.py
  apps/payments/views.py
  apps/search/views.py
  config/urls.py
  frontend/css/components/header.css
  frontend/js/main.js
  frontend/js/modules/search-suggest.js
  scripts/audit_copy_honesty.py
  scripts/classification_audit.py
  scripts/e2e_browser.py
  templates/403.html
  templates/403_csrf.html
  templates/404.html
  templates/429.html
  templates/500.html
  templates/base.html
  templates/cart/cart_detail.html
  templates/catalog/brand_list.html
  templates/catalog/category_detail.html
  templates/catalog/category_list.html
  templates/catalog/home.html
  templates/includes/footer.html
  templates/includes/header.html
  templates/orders/checkout_address.html
  templates/orders/checkout_review.html
  templates/orders/order_success.html
  templates/pages/about.html
  templates/pages/refunds.html
  templates/pages/terms.html
  templates/payments/razorpay_checkout.html
  tests/js/search_suggest.test.js
  tests/test_catalog_services.py
  tests/test_category_rules.py
  tests/test_copy_honesty.py
  tests/test_core.py
  tests/test_families_and_display_names.py
  tests/test_performance.py
  tests/test_spec_extractor.py
  tests/test_tax_mode_and_footing.py
  tests/test_views_catalog.py
  tests/test_views_category_spread.py
  tests/test_views_checkout.py
  tests/test_views_home.py
  docs/UI_FINDINGS.md
  docs/ui-review/pass1_unseen.md
  docs/phase-8a-report.md
```

All standing orders strictly observed. No git push was or will be performed.
