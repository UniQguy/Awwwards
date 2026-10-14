# Phase R6 Initial Defect Inventory & Baseline Audit
**Audit Date:** 2026-10-14  
**Status:** Baseline Established from Real Browser Screenshots

---

## 1. Visual & Layout Defects (Screenshots Viewed)

| ID | Page / Area | Viewport | Defect Description | Severity | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | `/c/smartphones/` (Marquee) | 1366x768, 390x844 | Marquee secondary pick plates render tiny product thumbnails (~25px high) inside massive grey plates; layout overlaps grid content below. | Critical | Resolved in WP1 (`docs/ui-review/r6/wp1/1366x768/category_smartphones.png`) |
| **DEF-02** | `/c/<slug>/` (Catalog Grid) | All | Product cards render as wide horizontal rectangular strips instead of square (1/1) plates; product photos do not fill 70-80% of plate area. | High | Resolved in WP1 (`docs/ui-review/r6/wp1/1366x768/cameras_page2.png`) |
| **DEF-03** | Global (Product Display Name) | All | Product titles strip brand from model name, producing incomplete model names (e.g., "Redmi 9" becomes just "9", Echo Dot and JBL Go 3 lose model words). | High | Resolved in WP1 (`apps/core/templatetags/core_tags.py`, test verified) |
| **DEF-04** | Global (Brand Parsing) | All | Multi-token brands lose casing (e.g. "CP PLUS" becomes "Cp"); titles with leading symbols (`®`, `™`, quotes, bullets) fail clean display. | Medium | Resolved in WP1 (`apps/catalog/services/brands.py`, allowlist updated) |
| **DEF-05** | Home (`/`) Hero Headline | 1366x768, 390x844 | Headline product cutouts render inside visible white rectangular boxed frames against warm paper; commas and period float disconnected after cutout boxes. | High | Resolved in WP1 (`docs/ui-review/r6/wp1/1366x768/home_hero.png`) |
| **DEF-06** | Home (`/`) Hero Layout | 1366x768 | Excessive dead band above hero headline; next section not visible on initial 1366x768 fold. Home scroll height is 15.4 viewports (11,845px) due to pinned giant chapters. | High | Open (WP3 Scope) |
| **DEF-07** | Header (Shop Menu) | 1366x768 | Shop menu dropdown is narrow; category listing counts column overflows and collides with category names on the right side. | High | Open (WP4 Scope) |
| **DEF-08** | Product Cards (Stock Badges) | All | Cards render redundant "IN STOCK" badges across majority of items instead of only alerting shoppers for "Only N left" and "Out of stock". | Medium | Resolved in WP1 (`templates/includes/stock_badge.html`) |
| **DEF-09** | `/c/cameras/?page=2` Filters | All | Min price filter field exhibits browser form restoration / stale values (e.g. 20000) when URL contains no price query parameters. Missing `autocomplete="off"`. | High | Resolved in WP1 (`tests/test_catalog_filters.py`) |
| **DEF-10** | Admin (`/admin/`) Navigation | Desktop | Two distinct navigation app sections titled "ACCOUNTS" without differentiation (Allauth Account vs Local Accounts). | Medium | Resolved in WP1 (`apps/accounts/apps.py`) |
| **DEF-11** | Admin (`/admin/`) Dashboard | Desktop | Today's revenue formatted as un-grouped raw number `₹2057.00` without Indian numeral grouping (`inr` filter). | Medium | Resolved in WP1 (`templates/admin/index.html`) |
| **DEF-12** | Admin & Dev Outbox | All | Leftover test data, `LogEntry` rows, and test emails from e2e scripts populate the database and `.emails/` directory. | Medium | Resolved in WP1 (Purged: 19 LogEntry -> 0, 4 Emails -> 0) |
| **DEF-13** | Global Sticky Header | All | Fixed/sticky header covers top of anchor-scrolled sections and page targets due to missing `scroll-padding-top`. | Medium | Resolved in WP1 (`frontend/css/layout.css`) |

---

## 2. Baseline Measurements

- **Python Tests Passing:** 289 tests (manage.py test)
- **Vitest Tests Passing:** 52 tests across 7 test files (npm test)
- **Home Page Scroll Height (1366x768):** 11,845 px (15.42 viewports)
- **Production Asset Chunk Sizes:**
  - `styles-Buin4GS3.css`: 104.64 kB (gzip: 17.57 kB)
  - `main-BKdM1wrH.js`: 19.54 kB (gzip: 6.05 kB)
  - `editorial-C-L9iGbC.js`: 158.96 kB (gzip: 58.30 kB)
  - `hero_webgl-D5r44q9I.js`: 621.90 kB (gzip: 157.98 kB)
  - `media_slot-BcDUG_bG.js`: 4.70 kB (gzip: 1.79 kB)
