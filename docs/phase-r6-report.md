# Phase R6 Final Report: The Shop Floor

> **Context**: Comprehensive University Faculty Examination & Archival Report for ELECTROCART (Phase R6: The Shop Floor).  
> **Repository Baseline Tag**: `pre-r6`  
> **Committed Quality Gates**: Zero hallucinated tools, zero invented products or ratings, 100% real browser screenshot evidence, zero visual slop, WCAG 2.1 AA verified, and complete audit coverage.

---

## 1. Audit Matrix

Every audit in the suite was executed against real Chromium browser contexts and Django runtime environments. Real command outputs and exit codes are recorded below:

| Audit Script | Command Line Executed | Exit Code | Defect Count | Evidence & Artifact Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Overlap & Occlusion Audit** | `python scripts/overlap_audit.py` | **0** | **0** | 0 section collisions, 0 plate deformities, 0 occlusions across 4 viewports x 7 pages (28 evaluations). |
| **Void & Reveal Audit** | `python scripts/void_audit.py` | **0** | **0** | 0 voids $>300\times300\text{px}$, 0 stuck reveal masks across Desktop (1456px) and Mobile (390px). |
| **Layout & Design Craft Audit** | `python scripts/layout_audit.py` | **0** | **0** | 0 defects across 8 viewports x 8 routes (64 checks). Report: [`reports/layout_audit.md`](../reports/layout_audit.md). |
| **Fold Density & Scale Audit** | `python scripts/fold_audit.py` | **0** | **0** | 0 failures across 21 checks (7 viewports x 3 pages). All key CTAs, prices, and titles visible above fold. |
| **CSS Token Discipline Audit** | `python scripts/css_audit.py` | **0** | **0** | 0 hardcoded colors outside `tokens.css`; 0 illegal `!important` declarations. |
| **WCAG 2.1 AA Contrast Audit** | `python scripts/verify_contrast.py` | **0** | **0** | All 10 chromatic category worlds pass WCAG 2.1 AA ($>4.5:1$ text, $>3.0:1$ UI components). |
| **Network Host Allowlist Audit** | `python scripts/allowlist_audit.py` | **0** | **0** | 0 unauthorized network requests; only `cdnjs`, `jsdelivr`, `m.media-amazon.com`, `self` contacted. |
| **Idle Stability Audit (Rule J)** | `python scripts/idle_check.py` | **0** | **0** | After load + 10s: 0 running animations, 0 DOM mutations in 5s window, 0 recurring timers. |
| **100% Offline Capability Audit** | `python scripts/offline_check.py` | **0** | **0** | 12 routes pass with 100% offline self-containment; local geometric SVG plates fall back cleanly. |
| **Full Commerce QA & Keyboard E2E** | `python scripts/full_qa.py` | **0** | **0** | 466 matrix evaluations verified clean; pure keyboard purchase walkthrough completed from Home to Invoice. |
| **Admin E2E Verification** | `python scripts/exercise_admin_e2e.py` | **0** | **0** | Product add, image upload, collection curate, order status transitions, CSV export, and demo cleanup verified. |
| **Auth & Email Lifecycle E2E** | `python scripts/exercise_auth_e2e.py` | **0** | **0** | User signup, verification link via `/dev/outbox/`, confirmation, login, logout, password reset flow verified. |
| **Commerce Enhancements E2E** | `python scripts/exercise_commerce_features.py` | **0** | **0** | Star glyphs, PIN estimator, coupons drawer, save-for-later, move-to-bag, recently viewed shelf verified. |
| **Full Django Unit Suite** | `python manage.py test` | **0** | **0** | **307 tests passed in 50.9s** (0 errors, 0 failures). |
| **Frontend Vitest Suite** | `npm test` | **0** | **0** | **57 unit tests passed across 8 test suites**. |

---

## 2. Loop-by-Loop Changes per Work Package (WP)

Each work package followed an empirical build-measure-critique cycle against Rule C and Standing Orders.

### WP0: Start Protocol, Baseline Metrics & Blind-Spot Audits
- **Defects Identified**: The legacy test suite had missed an overlapping marquee on category pages and 25px collapsed plate thumbnails.
- **Loop 1**: Authored `scripts/overlap_audit.py` to evaluate sibling bounding box collisions, `elementFromPoint` card reachability, and plate aspect ratios ($0.9 - 1.25$ with $\ge 70\%$ image coverage). Proved failure on the unpatched build with 46 defects identified. Recorded `pre-r6` baseline metrics. Tagged commit `2fc26c6`.

### WP1: Root Defect Corrections
- **Rule C Defects**: Plate aspect ratios deformed into wide horizontal strips; Redmi 9 titles duplicated the brand ("Redmi Redmi 9..."); CP PLUS parsed as "Cp"; floating punctuation commas; camera filter page retained stale ₹20,000 query in form input; admin showed duplicate "Accounts" headers; and sticky header obscured anchor targets.
- **Loop 1**: Restored `aspect-ratio: 1/1` square plates with `object-fit: contain` and 80% width containment in `cards.css` and `editorial-plate.css`.
- **Loop 2**: Upgraded `brand_detector.py` and `spec_extractor.py` to preserve multi-token brands with canonical casing ("CP PLUS"), strip leading bullet/trademark symbols (`®`, `™`), and eliminate brand duplication in display names.
- **Loop 3**: Bound trailing punctuation commas to preceding words with `.cutout-bound`, set `autocomplete="off"` on catalog filter inputs, assigned distinct `verbose_name` to Django Allauth vs Customer Accounts, and added `scroll-padding-top: var(--header-height)` to `tokens.css`. Tagged commit `2ddf4a9`.

### WP2: Research & Editorial Design Brief
- **Investigation**: Inspected architecture, typography ratios, and motion timing on Daylight Computer, Apple, and Samsung.
- **Loop 1**: Authored [`docs/INSPIRATION.md`](INSPIRATION.md) analyzing quiet editorial pacing, calm spatial contrast, and purposeful motion. Authored [`docs/DESIGN_BRIEF_R6.md`](DESIGN_BRIEF_R6.md) establishing exact shop floor blueprints. Tagged commit `5c42808`.

### WP4: Compact Mega-Menu & Header Architecture
- **Rule C Defects**: The old Shop menu count column overflowed and collided with category titles; lack of category preview made navigation abstract.
- **Loop 1**: Rebuilt the Shop dropdown as a native `<details class="shop-menu-details">` containing a 2-column 720px mega-menu. Left column displays category titles, world color swatches, and right-aligned tabular listing counts. Right column renders an interactive preview pane with starting prices (`from ₹...`), product cutouts, and direct links.
- **Loop 2**: Added full keyboard navigation (`ArrowDown`, `ArrowUp`, `Escape`, `Home`, `End`) in `menu-panel.js`.
- **Loop 3**: Connected the bottom edge of the header to a GPU-composited 2px progress thread (`#header-scroll-thread`) tracking scroll depth and active category world color. Tagged commit `db19bc5`.

### WP5: Category Page Utility Layout & Most-Rated Shelf
- **Rule C Defects**: Category marquee created empty voids $>300\times300\text{px}$ on desktop and pushed the catalog grid below the fold.
- **Loop 1**: Replaced the decorative banner with a compact editorial header featuring Fraunces typography, listing counts, and quick filter chips for top brands and budget tiers.
- **Loop 2**: Introduced a 6-card "Most Rated in [Category]" shelf with honest source attribution caption ("Selected by number of ratings on Amazon") and 1:1 collectible plates.
- **Loop 3**: Implemented deterministic multi-column catalog grid (4 columns at 1366px, 5 columns at 1920px, 2 columns on mobile) with zero overlap defects. Tagged commit `f32eb66`.

### WP6: Product Detail Page (PDP) Exhibition Architecture
- **Rule C Defects**: PDP media plinth was vertically oversized; no full-resolution inspection existed; technical specs lacked comparative context.
- **Loop 1**: Sized `.product-frame-mat` to near-square 1:1 aspect ratio with multiply blending on warm paper, adding an accessible corner Zoom trigger button.
- **Loop 2**: Implemented a native HTML5 `<dialog id="pdp-lightbox-dialog">` with backdrop blur, 1.75x pan-zoom, and Escape key dismissal. Added sticky scrollspy subnav (`#section-overview`, `#section-specs`, `#section-box`, `#section-compare`).
- **Loop 3**: Added structured "In the Box" manifest and a 4-column comparative specification matrix within the strict 15-query test budget. Added fly-to-bag animation and native `<dialog id="mini-bag-dialog">` confirmation modal. Tagged commit `7164f2e`.

### WP3: Calm Editorial Shop Floor Rebuild & Height Gate
- **Rule C Defects**: Legacy homepage stretched to 11,845px (15.4 viewports) across 6 pinned scroll-traps that hijacked native scroll physics.
- **Loop 1**: Completely removed all pinned stage scroll-traps (`.pinned-stage`, `.scroll-trap`, `.hero-pin-container`). Rebuilt hero with top-aligned Fraunces headline, single prominent cutout spotlight plate, and 4-thumbnail picker.
- **Loop 2**: Added horizontal scroll-snap category rail, exactly 3 composed category chapter monographs with lead and satellite cards, 2 curated story collections in a 2-column grid, a 4-bracket budget ladder, a 3-column "How Buying Works" section, and a quiet brand flow.
- **Loop 3**: Measured homepage scroll height at 1456x820 desktop: **4,474px** (5.45 viewports), strictly passing the $\le 4,608\text{px}$ 6-viewport height gate. Tagged commit `08f6ce8`.

### WP7: Motion System, Pinned SRI CDN Loader & Idle Check
- **Rule C Defects**: Missing SRI integrity on CDN scripts; idle CPU drain from WebGL and interval loops; unverified CDN failure recovery.
- **Loop 1**: Pinned GSAP 3.12.5 and ScrollTrigger via Cloudflare CDN with SHA-384 integrity and `defer`. Vendored matching copies in `static/vendor/gsap/` with `LICENSE.txt`. Authored external `cdn_fallback.js` that probes `window.gsap` after 2500ms and injects vendored assets if blocked.
- **Loop 2**: Removed continuous Three.js WebGL render loop and cutout cycling intervals.
- **Loop 3**: Verified idle silence via `scripts/idle_check.py` (0 running animations, 0 mutations, 0 timers during seconds 5–10). Tagged commit `510f18b`.

### WP8: Regression Quality Loop & Tap Target Optimization
- **Rule C Defects**: 63 tap target warnings in `layout_audit.py`; card height mismatch in `fold_audit.py`; Playwright strict mode click conflicts in admin/auth e2e.
- **Loop 1**: Added `.dense-list` and `.tag-list` to inline chip containers; enforced 44px min-dimensions on `.snap-rail-btn`, `.link-subtle`, and `.pdp-zoom-trigger-btn`. Reduced layout defects from 63 to 0.
- **Loop 2**: Aligned `fold_audit.py` to evaluate card width (200-260px) rather than card height, reflecting WP1.2's 1:1 plate geometry (documented in DEC-045). Tightened mobile PDP plinth to keep H1 and price above 844px fold.
- **Loop 3**: Created unit regression suite `tests/test_r6_shop_floor.py` with 13 comprehensive tests. Executed full test suites (307 Django tests, 57 Vitest tests). Tagged commit `2199e2d`.

---

## 3. Motion System & "What the Shopper Learns From It" (Rule D)

Every animation in ELECTROCART serves an editorial communication purpose. Banned effects (particles, glow, cursor followers, text scramble, bounce easing) have been eliminated.

| Motion Effect | Technical Implementation | What the Shopper Learns From It |
| :--- | :--- | :--- |
| **Composited Scroll Thread** | `header-scroll.js`, `transform: scaleX(...)` on GPU compositor. | **Depth & World**: The shopper learns their physical depth in the multi-category catalogue and the active category world color context. |
| **Collectible Plate 3D Tilt** | `collectible_cards.js`, slow $\pm 6^\circ$ 3D tilt with dynamic specular glare on Tier 1 fine pointer. | **Craft & Materiality**: The shopper learns the tactile three-dimensional geometry, industrial finish, and build quality of the electronic object. |
| **Chapter Entrances** | `editorial.js`, batched `ScrollTrigger.batch` (translateY 24px $\rightarrow$ 0, opacity 0 $\rightarrow$ 1, 0.45s). | **Editorial Hierarchy**: The shopper learns they have crossed into a new curated category chapter with distinct lead and satellite hardware selections. |
| **Fly-to-Bag & Badge Pulse** | `pdp_exhibition.js`, 48x48 thumbnail trajectory to `#header-bag-count` over 0.5s with subtle 1.1x pulse. | **Purchase Certainty**: The shopper receives immediate, unambiguous visual confirmation that their chosen unit has been safely placed in their shopping bag. |
| **Mini-Bag Confirmation Modal** | Native `<dialog id="mini-bag-dialog">`, backdrop dim, slide-in from edge. | **Commerce State**: The shopper learns the updated bag contents, subtotal, and immediate pathways to view the bag or proceed to checkout. |
| **Price Histogram Scrubbing** | `price_histogram.js`, stepped log scale with SVG bar highlight and live counts. | **Market Distribution**: The shopper learns the statistical distribution of catalog listings across price bands and the exact quantity meeting their budget. |
| **Hero Cutout Hover Reveal** | `editorial-cutout.css`, subtle vertical translate and border tint on noun tags. | **Curatorial Provenance**: The shopper learns which hardware items represent the core physical verbs of the catalogue (plugging in, putting on, listening with). |

---

## 4. Dead Code & Slop Removed

The following obsolete, decorative, or performance-degrading code was permanently excised:

1. **Pinned Stage Monograph Architecture**: Completely deleted 6 scroll-trapping pinned sections (`.pinned-stage`, `.scroll-trap`, `.hero-pin-container`) that previously forced 11,845px of vertical scrolling.
2. **Three.js WebGL Continuous Render Loop**: Removed active WebGL animation loop from the homepage hero, eliminating idle GPU wakeups and thermal drain.
3. **Looping Interval Timers**: Removed `setInterval` circular buffer cycles from `headline_cutouts.js`.
4. **Oversized Category Marquee**: Removed 170px stacked hero banner and unconstrained plate strips from `templates/catalog/category_detail.html`.
5. **Stale Filter State**: Removed form restoration retaining stale prices on camera pagination.
6. **Banned Decorative Slop**: Zero gradient blobs, particles, cursor followers, magnetic buttons, text scramble, bounce or elastic easing, parallax on utility pages, count-ups without meaning, looping decoration, or autoplay sound exist anywhere in the codebase.

---

## 5. Performance Measurements at 4x CPU Throttle (Rule E)

Evaluated in Chromium under 4x CPU throttling via Chrome DevTools Protocol (`Emulation.setCPUThrottlingRate: 4`) during scripted scrolls:

| Page Evaluated | Viewport | Long Tasks ($>100\text{ms}$) | p95 Frame Time | CLS Score | Document Scroll Height |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Home Monograph (`/`)** | 1366x768 | **0** | **33.40 ms** | 0.1166 | **4,555 px** ($\le 4,608\text{px}$ gate) |
| **Category Detail (`/c/smartphones/`)** | 1366x768 | **0** | **16.80 ms** | 0.0000 | 4,061 px |
| **Product Detail (`/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/`)** | 1366x768 | **0** | **16.80 ms** | 0.0000 | 3,464 px |

### Static Asset Chunk Sizes (Before vs After)

| Asset Chunk | R5 Baseline | R6 Final Pass | Difference / Optimization |
| :--- | :---: | :---: | :--- |
| **`styles.css`** | 126.85 kB | **127.13 kB** (gzip: 20.44 kB) | +0.28 kB (added mega-menu & lightbox tokens) |
| **`main.js`** | 21.40 kB | **21.60 kB** (gzip: 6.68 kB) | +0.20 kB (added dialog modal hooks) |
| **`editorial.js`** | 162.40 kB | **159.33 kB** (gzip: 58.11 kB) | **-3.07 kB** (excised WebGL render loops & slop) |
| **Self-Hosted Fonts (WOFF2)** | 390.41 kB | **390.41 kB** | Unchanged (Fraunces + Plus Jakarta Sans) |
| **External CDN Footprint** | 0 kB | **0 kB build weight** | Pinned GSAP + ScrollTrigger loaded via SRI CDN |

---

## 6. Pinned CDN Files Table (Rule F)

In accordance with Rule F, all external scripts are strictly pinned to exact versions, loaded with SHA-384 integrity attributes, and backed up with vendored local fallbacks.

| Pinned Script URL | Exact Version | SHA-384 SRI Hash | License | Vendored Local Path |
| :--- | :---: | :--- | :--- | :--- |
| `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js` | 3.12.5 | `sha384-g4NTh/Iv5PPU4xPyhEWqPcwtNXOvdaDI8LLnyYfyNZOjKJeYQyjzQ9X5275eBjpt` | GreenSock Standard / MIT compatible | `static/vendor/gsap/gsap.min.js` |
| `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js` | 3.12.5 | `sha384-Z3REaz79l2IaAZqJsSABtTbhjgOUYyV3p90XNnAPCSHg3EMTz1fouunq9WZRtj3d` | GreenSock Standard / MIT compatible | `static/vendor/gsap/ScrollTrigger.min.js` |

### Vendored Fallback Loader Architecture
- Loader script: `static/vendor/gsap/cdn_fallback.js` (loaded with `defer`).
- Operation: Checks for `window.gsap` after 2500ms. If `window.gsap` is undefined (CDN blocked or network partitioned), it dynamically injects the local vendored scripts and dispatches `window.dispatchEvent(new Event("gsap:ready"))`.
- Verified via `scripts/test_cdn_fallback.py` blocking `cdnjs.cloudflare.com`: the storefront seamlessly falls back and renders cleanly with zero errors.

---

## 7. Real Browser Screenshot Index (Rule A Verification)

Every screenshot below was captured using Playwright Chromium in headless mode, stored on disk, and verified by direct inspection:

| Viewport | Surface / Route | Screenshot File Path | Viewed Description & Rule C Verification |
| :---: | :--- | :--- | :--- |
| **1366x768** | Home Hero Top | `docs/ui-review/r6/after/1366x768/01_home_top.png` | Fraunces display headline with integrated noun cutout tags and no dead band above, flanked by a prominent 1:1 collectible plate with Redmi 9, honest attribution, and 4-thumbnail picker. |
| **1366x768** | Chapter 01 Shelf | `docs/ui-review/r6/after/1366x768/02_home_chapter_01.png` | Earphones & Headphones chapter spread with 4-card asymmetric layout (lead hero card on left, 3 satellite cards on right), right-aligned tabular INR prices, and honest attribution. |
| **1366x768** | Categories Index | `docs/ui-review/r6/after/1366x768/04_categories.png` | Comprehensive index of 10 category worlds with starting prices, product counts, and chromatic swatch indicators. |
| **1366x768** | Smartphones Detail | `docs/ui-review/r6/after/1366x768/05_category_smartphones.png` | Compact category header with quick brand and budget chips, followed by a 6-card "Most Rated" shelf with perfectly proportioned 1:1 plates and zero overlap defects. |
| **1366x768** | Product Detail | `docs/ui-review/r6/after/1366x768/08_product_page.png` | Sticky scrollspy subnav with persistent price and CTA, an expansive 1:1 exhibition plinth with zoom trigger, and structured commerce panel above the fold. |
| **1366x768** | Shop Mega-Menu | `docs/ui-review/r6/after/1366x768/10_shop_menu_open.png` | 2-column 720px mega-menu displaying category swatches, titles, right-aligned tabular counts, starting prices, and interactive preview pane with warm paper plate and explore button. |
| **1366x768** | Shopping Bag | `docs/ui-review/r6/after/1366x768/13_cart_with_items.png` | Shopping bag showing free delivery progress bar, 1:1 near-square plate thumbnail, quantity controls, "Save for Later" actions, and right-aligned order summary with ₹269 item total. |
| **1366x768** | Checkout Review | `docs/ui-review/r6/after/1366x768/14_checkout_review.png` | Checkout review screen showing 3-step breadcrumb stepper, active 15-minute stock hold reservation card, formatted delivery address, and order totals. |
| **1366x768** | Statutory Invoice | `docs/ui-review/r6/after/1366x768/15_invoice_html.png` | Statutory Bill of Supply under Rule 46 CGST Rules, 2017 with invoice number EC-BOS-2026-27-00021, buyer address, HSN 8504, QTY, unit price ₹859, and words total. |
| **1366x768** | Mini-Bag Dialog | `docs/ui-review/r6/after/1366x768/16_mini_bag_open.png` | Native `<dialog id="mini-bag-dialog">` modal open over dimmed backdrop with "Added to Bag" confirmation, thumbnail, title, price ₹269, and action buttons. |
| **390x844** | Mobile Home Top | `docs/ui-review/r6/after/390x844/01_home_top.png` | Mobile hero layout with responsive Fraunces headline, stacked action buttons, and centered collectible plate above the fold. |
| **390x844** | Mobile Product Detail | `docs/ui-review/r6/after/390x844/08_product_page.png` | Compact mobile product sheet with capped 200px plinth, product H1, star ratings, and price badge positioned well above the 844px mobile fold. |
| **390x844** | Mobile Checkout Review | `docs/ui-review/r6/after/390x844/14_checkout_review.png` | Mobile checkout review screen displaying 3-step progress breadcrumbs, active stock hold banner, and address cards with zero horizontal scroll overflow. |
| **390x844** | Mobile Mini-Bag Dialog | `docs/ui-review/r6/after/390x844/16_mini_bag_open.png` | Mobile mini-bag modal popping up over dimmed backdrop with checkmark confirmation, thumbnail, price ₹269, and stacked full-width "View Bag" and "Checkout" buttons. |

---

## 8. Honest Statement: What the Shop Floor Does and Does Not Do

### What ELECTROCART Does:
1. **Curated Catalogue with Technical Provenance**: Catalogs 6,707 real consumer electronic listings across 10 chromatic category worlds, preserving exact raw marketplace titles alongside curated display names and canonical brand names.
2. **Honest Attribution**: Displays real Amazon India star ratings and review volume counts with transparent attribution (`Selected by number of ratings on Amazon`).
3. **Deterministic Inventory & Stock Holds**: Executes concurrency-safe inventory holds using atomic conditional SQL updates with a 15-minute stock reservation window.
4. **Statutory Indian Tax Compliance**: Computes exact CGST + SGST (intrastate) and IGST (interstate) breakdowns based on verified HSN codes (8504, 8517, 8518, 8528) and renders statutory Bills of Supply and GST Tax Invoices in HTML and downloadable PDF formats.
5. **Privacy-First Local Storage**: Maintains "Recently Viewed" products entirely in browser `localStorage` without tracking cookies, beacons, or third-party telemetries.
6. **100% Offline Resilience**: Runs completely disconnected from the public internet with self-hosted WOFF2 fonts and local SVG geometric plates.

### What ELECTROCART Does Not Do:
1. **Does Not Fabricate Store Reviews**: Does not invent user testimonials, fake star ratings, or customer quotes.
2. **Does Not Run Unaudited Background Jobs**: Zero background daemon processes remain running after page load.
3. **Does Not Charge Live Credit Cards**: Razorpay gateway operates in test/mock mode using sample keys.
4. **Does Not Hijack Utility Scrolling**: Lenis smooth scrolling is strictly confined to editorial catalog routes on fine-pointer desktop screens; utility routes (`/cart/`, `/checkout/`, `/account/`) use 100% native browser scrolling.

---

## 9. Top Five Remaining Weaknesses & Faculty Examination Defense

| # | Potential Examiner Probe | Project Defense / Architectural Rationale |
| :-: | :--- | :--- |
| **1** | *"Why allow external CDN scripts for GSAP instead of bundling everything via Vite?"* | **Defense**: CDN hosting provides zero build weight and browser caching across websites. In accordance with Rule F, security and network dependencies are mitigated by strict Subresource Integrity (`integrity="sha384-..."`), strict CSP allowlisting (no wildcards), and an external fallback loader that injects vendored local copies (`static/vendor/gsap/`) if the CDN is unreachable. Verified 100% offline via `offline_check.py`. |
| **2** | *"Why are product specifications stored in a JSONField rather than normalized relational tables?"* | **Defense**: Consumer electronics span wildly disparate attribute sets (e.g., HDMI bandwidth vs. headphone impedance vs. camera sensor size). Relational EAV schemas incur massive JOIN overhead and sparse tables. Storing validated key-value pairs in a JSONField with Django prefetching preserves sub-millisecond query performance while keeping queries bounded well under the 15-query test budget. |
| **3** | *"Why is the stock reservation window fixed at exactly 15 minutes?"* | **Defense**: High-demand electronics sales require balancing customer cart completion against inventory hoarding. A 15-minute atomic reservation window mirrors industry standards (Ticketmaster, Apple Store) and is enforced via database timestamps and periodic cleanup tasks. |
| **4** | *"Why use ReportLab instead of WeasyPrint for statutory PDF invoices?"* | **Defense**: WeasyPrint requires complex external C system libraries (Pango, Cairo, GObject) that frequently fail on Windows host environments and minimal container runtimes. ReportLab is 100% self-contained pure Python with zero native dependencies, ensuring statutory invoice generation works reliably on any operating system. |
| **5** | *"Why use native `<dialog>` elements for lightboxes and mini-bag drawers rather than standard JavaScript modal libraries?"* | **Defense**: Native HTML5 `<dialog>` elements provide native focus trapping, accessible backdrop rendering (`::backdrop`), built-in Escape key dismiss behavior, and top-layer stacking without third-party dependencies, layout thrashing, or ARIA accessibility violations. |

---

## 10. Action Required from Owner Before Commercial Production

1. **Replace Placeholder Sample Copy**: Replace academic demonstration policy banners on `/legal/terms/`, `/legal/privacy/`, `/legal/shipping/`, and `/legal/refunds/` with formal legal counsel-approved text.
2. **Configure Production API Keys**: Supply live Razorpay Key ID and Secret in production environment variables (`DJANGO_RAZORPAY_KEY_ID`, `DJANGO_RAZORPAY_KEY_SECRET`).
3. **Configure Live SMTP Mail Server**: Switch `EMAIL_MODE` from `file` to `smtp` and supply live host credentials in production settings.
4. **Enable SSL/TLS Hardening**: Set `DEBUG=False`, `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, and `SECURE_HSTS_SECONDS=31536000` behind a production reverse proxy (Nginx / Cloudflare).

---

## 11. Exact Git Difference Statistics (`git diff --stat pre-r6..HEAD`)

```text
 apps/accounts/apps.py                              |   7 +
 apps/catalog/data/brand_allowlist.txt              |   7 +
 .../management/commands/rebuild_display_names.py   |  23 +-
 apps/catalog/services/brands.py                    |   9 +-
 apps/catalog/services/category_nav.py              |  88 ++
 apps/catalog/services/editorial.py                 |  22 +-
 apps/catalog/services/parsing.py                   |   3 +-
 apps/catalog/views.py                              | 108 ++-
 apps/core/context_processors.py                    |  11 +-
 apps/core/templatetags/core_tags.py                |  13 +-
 config/settings/base.py                            |   2 +
 docs/DECISIONS.md                                  |  80 +-
 docs/DESIGN_BRIEF_R6.md                            |  57 ++
 docs/EXAM_RUNBOOK.md                               |   2 +-
 docs/FEATURE_MATRIX.md                             |   2 +-
 docs/INSPIRATION.md                                |  54 ++
 docs/MOTION.md                                     |  42 +
 docs/phase-r6-report.md                            | 560 +++++++++++++
 docs/ui-review/admin_e2e/01_admin_login.png        | Bin 13371 -> 13362 bytes
 .../admin_e2e/02_admin_index_dashboard.png         | Bin 87495 -> 53803 bytes
 docs/ui-review/admin_e2e/03_product_add_form.png   | Bin 70481 -> 72779 bytes
 docs/ui-review/admin_e2e/04_product_created.png    | Bin 132362 -> 137157 bytes
 .../admin_e2e/05_product_editing_with_media.png    | Bin 73485 -> 75951 bytes
 docs/ui-review/admin_e2e/05b_product_edited.png    | Bin 89025 -> 92551 bytes
 .../ui-review/admin_e2e/06_collection_add_form.png | Bin 69933 -> 71642 bytes
 .../ui-review/admin_e2e/06b_collection_created.png | Bin 107558 -> 111918 bytes
 .../admin_e2e/07_storefront_collection_visible.png | Bin 167047 -> 176271 bytes
 docs/ui-review/admin_e2e/08_orders_changelist.png  | Bin 133668 -> 135866 bytes
 .../admin_e2e/09_order_detail_readonly.png         | Bin 77682 -> 79479 bytes
 .../admin_e2e/10_product_delete_confirm.png        | Bin 58787 -> 60506 bytes
 docs/ui-review/admin_e2e/11_product_deleted.png    | Bin 78937 -> 82960 bytes
 docs/ui-review/admin_e2e/orders_export.csv         |   2 +-
 .../auth_e2e/01_signup_verification_sent.png       | Bin 58539 -> 79367 bytes
 docs/ui-review/auth_e2e/02_outbox_list.png         | Bin 89499 -> 88007 bytes
 .../auth_e2e/03_outbox_detail_confirmation.png     | Bin 60708 -> 60286 bytes
 docs/ui-review/auth_e2e/04_email_confirmed.png     | Bin 65782 -> 57537 bytes
 docs/ui-review/auth_e2e/05_login_success.png       | Bin 0 -> 175109 bytes
 docs/ui-review/auth_e2e/06_account_dashboard.png   | Bin 0 -> 80771 bytes
 docs/ui-review/auth_e2e/07_logged_out.png          | Bin 0 -> 169993 bytes
 docs/ui-review/auth_e2e/08_password_reset_sent.png | Bin 0 -> 76507 bytes
 docs/ui-review/auth_e2e/09_outbox_detail_reset.png | Bin 0 -> 62565 bytes
 .../auth_e2e/10_password_reset_complete.png        | Bin 53213 -> 73599 bytes
 .../11_login_with_new_password_success.png         | Bin 184413 -> 174625 bytes
 .../01_pdp_honest_rating_and_pincode.png           | Bin 182388 -> 176061 bytes
 .../commerce_features/02_pdp_active_coupons.png    | Bin 182388 -> 176061 bytes
 .../commerce_features/03_cart_saved_for_later.png  | Bin 66054 -> 66067 bytes
 .../commerce_features/03b_cart_moved_to_bag.png    | Bin 152482 -> 177979 bytes
 .../04_pdp_recently_viewed_row.png                 | Bin 77622 -> 81532 bytes
 .../05_cart_recently_viewed_row.png                | Bin 97683 -> 142094 bytes
 .../fold_audit/category_detail_1093x614.png        | Bin 117736 -> 188572 bytes
 .../fold_audit/category_detail_1229x691.png        | Bin 118675 -> 185279 bytes
 .../fold_audit/category_detail_1366x768.png        | Bin 129070 -> 219639 bytes
 .../fold_audit/category_detail_1440x900.png        | Bin 134090 -> 240050 bytes
 .../fold_audit/category_detail_1536x864.png        | Bin 133900 -> 238846 bytes
 .../fold_audit/category_detail_1920x1080.png       | Bin 170800 -> 276415 bytes
 .../fold_audit/category_detail_390x844.png         | Bin 85673 -> 90377 bytes
 docs/ui-review/fold_audit/home_1093x614.png        | Bin 104168 -> 116016 bytes
 docs/ui-review/fold_audit/home_1229x691.png        | Bin 120146 -> 138447 bytes
 docs/ui-review/fold_audit/home_1366x768.png        | Bin 146816 -> 160194 bytes
 docs/ui-review/fold_audit/home_1440x900.png        | Bin 152678 -> 173958 bytes
 docs/ui-review/fold_audit/home_1536x864.png        | Bin 153069 -> 173131 bytes
 docs/ui-review/fold_audit/home_1920x1080.png       | Bin 162229 -> 195831 bytes
 docs/ui-review/fold_audit/home_390x844.png         | Bin 91691 -> 99096 bytes
 .../fold_audit/product_detail_1093x614.png         | Bin 143386 -> 137693 bytes
 .../fold_audit/product_detail_1229x691.png         | Bin 153360 -> 157002 bytes
 .../fold_audit/product_detail_1366x768.png         | Bin 164786 -> 169948 bytes
 .../fold_audit/product_detail_1440x900.png         | Bin 179272 -> 177741 bytes
 .../fold_audit/product_detail_1536x864.png         | Bin 178999 -> 175728 bytes
 .../fold_audit/product_detail_1920x1080.png        | Bin 196391 -> 202587 bytes
 .../fold_audit/product_detail_390x844.png          | Bin 109239 -> 82564 bytes
 docs/ui-review/r6/after/1366x768/01_home_top.png   | Bin 0 -> 194168 bytes
 .../r6/after/1366x768/02_home_chapter_01.png       | Bin 0 -> 149194 bytes
 .../r6/after/1366x768/02_home_chapter_02.png       | Bin 0 -> 166431 bytes
 .../r6/after/1366x768/02_home_chapter_03.png       | Bin 0 -> 63861 bytes
 .../ui-review/r6/after/1366x768/03_home_footer.png | Bin 0 -> 91628 bytes
 docs/ui-review/r6/after/1366x768/04_categories.png | Bin 0 -> 52211 bytes
 .../r6/after/1366x768/05_category_smartphones.png  | Bin 0 -> 219639 bytes
 .../r6/after/1366x768/06_category_speakers.png     | Bin 0 -> 194277 bytes
 .../after/1366x768/07_category_cameras_page2.png   | Bin 0 -> 168928 bytes
 .../r6/after/1366x768/08_product_page.png          | Bin 0 -> 169948 bytes
 docs/ui-review/r6/after/1366x768/09_cart.png       | Bin 0 -> 39409 bytes
 .../r6/after/1366x768/10_shop_menu_open.png        | Bin 0 -> 194214 bytes
 .../ui-review/r6/after/1366x768/11_admin_index.png | Bin 0 -> 43462 bytes
 docs/ui-review/r6/after/1366x768/12_dev_outbox.png | Bin 0 -> 81245 bytes
 .../r6/after/1366x768/13_cart_with_items.png       | Bin 0 -> 92411 bytes
 .../r6/after/1366x768/14_checkout_review.png       | Bin 0 -> 84706 bytes
 .../r6/after/1366x768/15_invoice_html.png          | Bin 0 -> 88469 bytes
 .../r6/after/1366x768/16_mini_bag_open.png         | Bin 0 -> 198838 bytes
 docs/ui-review/r6/after/1536x864/01_home_top.png   | Bin 0 -> 175658 bytes
 .../r6/after/1536x864/02_home_chapter_01.png       | Bin 0 -> 165753 bytes
 .../r6/after/1536x864/02_home_chapter_02.png       | Bin 0 -> 198465 bytes
 .../r6/after/1536x864/02_home_chapter_03.png       | Bin 0 -> 102934 bytes
 .../ui-review/r6/after/1536x864/03_home_footer.png | Bin 0 -> 93468 bytes
 docs/ui-review/r6/after/1536x864/04_categories.png | Bin 0 -> 54246 bytes
 .../r6/after/1536x864/05_category_smartphones.png  | Bin 0 -> 238846 bytes
 .../r6/after/1536x864/06_category_speakers.png     | Bin 0 -> 214091 bytes
 .../after/1536x864/07_category_cameras_page2.png   | Bin 0 -> 187183 bytes
 .../r6/after/1536x864/08_product_page.png          | Bin 0 -> 175728 bytes
 docs/ui-review/r6/after/1536x864/09_cart.png       | Bin 0 -> 40918 bytes
 .../r6/after/1536x864/10_shop_menu_open.png        | Bin 0 -> 212940 bytes
 .../ui-review/r6/after/1536x864/11_admin_index.png | Bin 0 -> 50731 bytes
 docs/ui-review/r6/after/1536x864/12_dev_outbox.png | Bin 0 -> 81643 bytes
 .../r6/after/1536x864/13_cart_with_items.png       | Bin 0 -> 151880 bytes
 .../r6/after/1536x864/14_checkout_review.png       | Bin 0 -> 112291 bytes
 .../r6/after/1536x864/15_invoice_html.png          | Bin 0 -> 106228 bytes
 .../r6/after/1536x864/16_mini_bag_open.png         | Bin 0 -> 207331 bytes
 docs/ui-review/r6/after/1920x1080/01_home_top.png  | Bin 0 -> 197109 bytes
 .../r6/after/1920x1080/02_home_chapter_01.png      | Bin 0 -> 243838 bytes
 .../r6/after/1920x1080/02_home_chapter_02.png      | Bin 0 -> 250862 bytes
 .../r6/after/1920x1080/02_home_chapter_03.png      | Bin 0 -> 182705 bytes
 .../r6/after/1920x1080/03_home_footer.png          | Bin 0 -> 128546 bytes
 .../ui-review/r6/after/1920x1080/04_categories.png | Bin 0 -> 128093 bytes
 .../r6/after/1920x1080/05_category_smartphones.png | Bin 0 -> 287605 bytes
 .../r6/after/1920x1080/06_category_speakers.png    | Bin 0 -> 262671 bytes
 .../after/1920x1080/07_category_cameras_page2.png  | Bin 0 -> 275903 bytes
 .../r6/after/1920x1080/08_product_page.png         | Bin 0 -> 202587 bytes
 docs/ui-review/r6/after/1920x1080/09_cart.png      | Bin 0 -> 46651 bytes
 .../r6/after/1920x1080/10_shop_menu_open.png       | Bin 0 -> 236497 bytes
 .../r6/after/1920x1080/11_admin_index.png          | Bin 0 -> 64073 bytes
 .../ui-review/r6/after/1920x1080/12_dev_outbox.png | Bin 0 -> 84920 bytes
 .../r6/after/1920x1080/13_cart_with_items.png      | Bin 0 -> 185717 bytes
 .../r6/after/1920x1080/14_checkout_review.png      | Bin 0 -> 127108 bytes
 .../r6/after/1920x1080/15_invoice_html.png         | Bin 0 -> 111145 bytes
 .../r6/after/1920x1080/16_mini_bag_open.png        | Bin 0 -> 238514 bytes
 docs/ui-review/r6/after/390x844/01_home_top.png    | Bin 0 -> 99077 bytes
 .../r6/after/390x844/02_home_chapter_01.png        | Bin 0 -> 65355 bytes
 .../r6/after/390x844/02_home_chapter_02.png        | Bin 0 -> 84521 bytes
 .../r6/after/390x844/02_home_chapter_03.png        | Bin 0 -> 55631 bytes
 docs/ui-review/r6/after/390x844/03_home_footer.png | Bin 0 -> 47982 bytes
 docs/ui-review/r6/after/390x844/04_categories.png  | Bin 0 -> 51843 bytes
 .../r6/after/390x844/05_category_smartphones.png   | Bin 0 -> 93387 bytes
 .../r6/after/390x844/06_category_speakers.png      | Bin 0 -> 95387 bytes
 .../r6/after/390x844/07_category_cameras_page2.png | Bin 0 -> 49341 bytes
 .../ui-review/r6/after/390x844/08_product_page.png | Bin 0 -> 82545 bytes
 docs/ui-review/r6/after/390x844/09_cart.png        | Bin 0 -> 42228 bytes
 .../r6/after/390x844/10_shop_menu_open.png         | Bin 0 -> 75073 bytes
 docs/ui-review/r6/after/390x844/11_admin_index.png | Bin 0 -> 33276 bytes
 docs/ui-review/r6/after/390x844/12_dev_outbox.png  | Bin 0 -> 42740 bytes
 .../r6/after/390x844/13_cart_with_items.png        | Bin 0 -> 58183 bytes
 .../r6/after/390x844/14_checkout_review.png        | Bin 0 -> 64080 bytes
 .../ui-review/r6/after/390x844/15_invoice_html.png | Bin 0 -> 61143 bytes
 .../r6/after/390x844/16_mini_bag_open.png          | Bin 0 -> 103860 bytes
 docs/ui-review/r6/before/1366x768/01_home_top.png  | Bin 0 -> 143985 bytes
 .../r6/before/1366x768/02_home_chapter_01.png      | Bin 0 -> 131738 bytes
 .../r6/before/1366x768/02_home_chapter_02.png      | Bin 0 -> 279892 bytes
 .../r6/before/1366x768/02_home_chapter_03.png      | Bin 0 -> 272311 bytes
 .../r6/before/1366x768/02_home_chapter_04.png      | Bin 0 -> 212766 bytes
 .../r6/before/1366x768/02_home_chapter_05.png      | Bin 0 -> 165694 bytes
 .../r6/before/1366x768/02_home_chapter_06.png      | Bin 0 -> 221566 bytes
 .../r6/before/1366x768/03_home_footer.png          | Bin 0 -> 68479 bytes
 .../ui-review/r6/before/1366x768/04_categories.png | Bin 0 -> 112990 bytes
 .../r6/before/1366x768/05_category_smartphones.png | Bin 0 -> 129070 bytes
 .../r6/before/1366x768/06_category_speakers.png    | Bin 0 -> 166316 bytes
 .../before/1366x768/07_category_cameras_page2.png  | Bin 0 -> 135101 bytes
 .../r6/before/1366x768/08_product_page.png         | Bin 0 -> 178631 bytes
 docs/ui-review/r6/before/1366x768/09_cart.png      | Bin 0 -> 39409 bytes
 .../r6/before/1366x768/10_shop_menu_open.png       | Bin 0 -> 172620 bytes
 .../r6/before/1366x768/11_admin_index.png          | Bin 0 -> 46346 bytes
 .../ui-review/r6/before/1366x768/12_dev_outbox.png | Bin 0 -> 56403 bytes
 docs/ui-review/r6/before/390x844/01_home_top.png   | Bin 0 -> 93299 bytes
 .../r6/before/390x844/02_home_chapter_01.png       | Bin 0 -> 67696 bytes
 .../r6/before/390x844/02_home_chapter_02.png       | Bin 0 -> 78374 bytes
 .../r6/before/390x844/02_home_chapter_03.png       | Bin 0 -> 106046 bytes
 .../r6/before/390x844/02_home_chapter_04.png       | Bin 0 -> 89623 bytes
 .../r6/before/390x844/02_home_chapter_05.png       | Bin 0 -> 69091 bytes
 .../r6/before/390x844/02_home_chapter_06.png       | Bin 0 -> 84955 bytes
 .../ui-review/r6/before/390x844/03_home_footer.png | Bin 0 -> 48141 bytes
 docs/ui-review/r6/before/390x844/04_categories.png | Bin 0 -> 73625 bytes
 .../r6/before/390x844/05_category_smartphones.png  | Bin 0 -> 85673 bytes
 .../r6/before/390x844/06_category_speakers.png     | Bin 0 -> 112394 bytes
 .../before/390x844/07_category_cameras_page2.png   | Bin 0 -> 33845 bytes
 .../r6/before/390x844/08_product_page.png          | Bin 0 -> 108762 bytes
 docs/ui-review/r6/before/390x844/09_cart.png       | Bin 0 -> 48848 bytes
 .../r6/before/390x844/10_shop_menu_open.png        | Bin 0 -> 100855 bytes
 .../ui-review/r6/before/390x844/11_admin_index.png | Bin 0 -> 33414 bytes
 docs/ui-review/r6/before/390x844/12_dev_outbox.png | Bin 0 -> 39804 bytes
 docs/ui-review/r6/wp1/1366x768/cameras_page2.png   | Bin 0 -> 168067 bytes
 .../r6/wp1/1366x768/category_smartphones.png       | Bin 0 -> 137502 bytes
 docs/ui-review/r6/wp1/1366x768/home_hero.png       | Bin 0 -> 140027 bytes
 docs/ui-review/r6/wp1/1536x864/cameras_page2.png   | Bin 0 -> 213618 bytes
 .../r6/wp1/1536x864/category_smartphones.png       | Bin 0 -> 144227 bytes
 docs/ui-review/r6/wp1/1536x864/home_hero.png       | Bin 0 -> 158497 bytes
 docs/ui-review/r6/wp1/1920x1080/cameras_page2.png  | Bin 0 -> 274390 bytes
 .../r6/wp1/1920x1080/category_smartphones.png      | Bin 0 -> 164969 bytes
 docs/ui-review/r6/wp1/1920x1080/home_hero.png      | Bin 0 -> 187341 bytes
 docs/ui-review/r6/wp1/390x844/cameras_page2.png    | Bin 0 -> 33845 bytes
 .../r6/wp1/390x844/category_smartphones.png        | Bin 0 -> 82977 bytes
 docs/ui-review/r6/wp1/390x844/home_hero.png        | Bin 0 -> 94425 bytes
 docs/ui-review/r6/wp1/test_cutout_blend.png        | Bin 0 -> 125467 bytes
 docs/ui-review/r6/wp3/1366x768/home_budget.png     | Bin 0 -> 99897 bytes
 .../r6/wp3/1366x768/home_buying_brands.png         | Bin 0 -> 101366 bytes
 docs/ui-review/r6/wp3/1366x768/home_chapters.png   | Bin 0 -> 165494 bytes
 docs/ui-review/r6/wp3/1366x768/home_hero.png       | Bin 0 -> 158978 bytes
 docs/ui-review/r6/wp3/1366x768/home_snap_rail.png  | Bin 0 -> 108387 bytes
 docs/ui-review/r6/wp3/1366x768/home_stories.png    | Bin 0 -> 101199 bytes
 .../r6/wp3/1366x768/home_stories_budget.png        | Bin 0 -> 99983 bytes
 docs/ui-review/r6/wp3/1536x864/home_budget.png     | Bin 0 -> 114242 bytes
 .../r6/wp3/1536x864/home_buying_brands.png         | Bin 0 -> 110870 bytes
 docs/ui-review/r6/wp3/1536x864/home_chapters.png   | Bin 0 -> 182926 bytes
 docs/ui-review/r6/wp3/1536x864/home_hero.png       | Bin 0 -> 174533 bytes
 docs/ui-review/r6/wp3/1536x864/home_snap_rail.png  | Bin 0 -> 128823 bytes
 docs/ui-review/r6/wp3/1536x864/home_stories.png    | Bin 0 -> 109895 bytes
 .../r6/wp3/1536x864/home_stories_budget.png        | Bin 0 -> 115289 bytes
 docs/ui-review/r6/wp3/1920x1080/home_budget.png    | Bin 0 -> 134301 bytes
 .../r6/wp3/1920x1080/home_buying_brands.png        | Bin 0 -> 123614 bytes
 docs/ui-review/r6/wp3/1920x1080/home_chapters.png  | Bin 0 -> 208468 bytes
 docs/ui-review/r6/wp3/1920x1080/home_hero.png      | Bin 0 -> 199167 bytes
 docs/ui-review/r6/wp3/1920x1080/home_snap_rail.png | Bin 0 -> 186157 bytes
 docs/ui-review/r6/wp3/1920x1080/home_stories.png   | Bin 0 -> 129850 bytes
 .../r6/wp3/1920x1080/home_stories_budget.png       | Bin 0 -> 136692 bytes
 docs/ui-review/r6/wp3/390x844/home_budget.png      | Bin 0 -> 53920 bytes
 .../r6/wp3/390x844/home_buying_brands.png          | Bin 0 -> 57232 bytes
 docs/ui-review/r6/wp3/390x844/home_chapters.png    | Bin 0 -> 87766 bytes
 docs/ui-review/r6/wp3/390x844/home_hero.png        | Bin 0 -> 101065 bytes
 docs/ui-review/r6/wp3/390x844/home_snap_rail.png   | Bin 0 -> 59684 bytes
 docs/ui-review/r6/wp3/390x844/home_stories.png     | Bin 0 -> 69807 bytes
 .../r6/wp3/390x844/home_stories_budget.png         | Bin 0 -> 56338 bytes
 docs/ui-review/r6/wp4/1366x768/header_default.png  | Bin 0 -> 140027 bytes
 docs/ui-review/r6/wp4/1366x768/mega_menu_hover.png | Bin 0 -> 191387 bytes
 docs/ui-review/r6/wp4/1366x768/mega_menu_open.png  | Bin 0 -> 183774 bytes
 docs/ui-review/r6/wp4/1536x864/header_default.png  | Bin 0 -> 158497 bytes
 docs/ui-review/r6/wp4/1536x864/mega_menu_hover.png | Bin 0 -> 211683 bytes
 docs/ui-review/r6/wp4/1536x864/mega_menu_open.png  | Bin 0 -> 203771 bytes
 docs/ui-review/r6/wp4/1920x1080/header_default.png | Bin 0 -> 187341 bytes
 .../ui-review/r6/wp4/1920x1080/mega_menu_hover.png | Bin 0 -> 237922 bytes
 docs/ui-review/r6/wp4/1920x1080/mega_menu_open.png | Bin 0 -> 230253 bytes
 docs/ui-review/r6/wp4/390x844/header_default.png   | Bin 0 -> 117682 bytes
 docs/ui-review/r6/wp4/390x844/mega_menu_open.png   | Bin 0 -> 90241 bytes
 .../r6/wp5/1366x768/category_filtered.png          | Bin 0 -> 165473 bytes
 docs/ui-review/r6/wp5/1366x768/category_page2.png  | Bin 0 -> 138062 bytes
 docs/ui-review/r6/wp5/1366x768/category_shelf.png  | Bin 0 -> 148386 bytes
 .../r6/wp5/1536x864/category_filtered.png          | Bin 0 -> 142369 bytes
 docs/ui-review/r6/wp5/1536x864/category_page2.png  | Bin 0 -> 160163 bytes
 docs/ui-review/r6/wp5/1536x864/category_shelf.png  | Bin 0 -> 159208 bytes
 .../r6/wp5/1920x1080/category_filtered.png         | Bin 0 -> 166870 bytes
 docs/ui-review/r6/wp5/1920x1080/category_page2.png | Bin 0 -> 172357 bytes
 docs/ui-review/r6/wp5/1920x1080/category_shelf.png | Bin 0 -> 213076 bytes
 .../ui-review/r6/wp5/390x844/category_filtered.png | Bin 0 -> 51754 bytes
 docs/ui-review/r6/wp5/390x844/category_page2.png   | Bin 0 -> 49341 bytes
 docs/ui-review/r6/wp5/390x844/category_shelf.png   | Bin 0 -> 77555 bytes
 docs/ui-review/r6/wp6/1366x768/pdp_compare.png     | Bin 0 -> 91721 bytes
 docs/ui-review/r6/wp6/1366x768/pdp_lightbox.png    | Bin 0 -> 123596 bytes
 docs/ui-review/r6/wp6/1366x768/pdp_overview.png    | Bin 0 -> 139369 bytes
 docs/ui-review/r6/wp6/1366x768/pdp_specs_box.png   | Bin 0 -> 123872 bytes
 docs/ui-review/r6/wp6/1536x864/pdp_compare.png     | Bin 0 -> 102437 bytes
 docs/ui-review/r6/wp6/1536x864/pdp_lightbox.png    | Bin 0 -> 140640 bytes
 docs/ui-review/r6/wp6/1536x864/pdp_overview.png    | Bin 0 -> 145245 bytes
 docs/ui-review/r6/wp6/1536x864/pdp_specs_box.png   | Bin 0 -> 129433 bytes
 docs/ui-review/r6/wp6/1920x1080/pdp_compare.png    | Bin 0 -> 155844 bytes
 docs/ui-review/r6/wp6/1920x1080/pdp_lightbox.png   | Bin 0 -> 200712 bytes
 docs/ui-review/r6/wp6/1920x1080/pdp_overview.png   | Bin 0 -> 172655 bytes
 docs/ui-review/r6/wp6/1920x1080/pdp_specs_box.png  | Bin 0 -> 142897 bytes
 docs/ui-review/r6/wp6/390x844/pdp_compare.png      | Bin 0 -> 49791 bytes
 docs/ui-review/r6/wp6/390x844/pdp_lightbox.png     | Bin 0 -> 77474 bytes
 docs/ui-review/r6/wp6/390x844/pdp_overview.png     | Bin 0 -> 69381 bytes
 docs/ui-review/r6/wp6/390x844/pdp_specs_box.png    | Bin 0 -> 62525 bytes
 docs/ui-review/r6/wp7/category_1366x768.png        | Bin 0 -> 219639 bytes
 docs/ui-review/r6/wp7/category_1536x864.png        | Bin 0 -> 238846 bytes
 docs/ui-review/r6/wp7/category_1920x1080.png       | Bin 0 -> 276415 bytes
 docs/ui-review/r6/wp7/category_390x844.png         | Bin 0 -> 93387 bytes
 docs/ui-review/r6/wp7/home_1366x768.png            | Bin 0 -> 158131 bytes
 docs/ui-review/r6/wp7/home_1536x864.png            | Bin 0 -> 175672 bytes
 docs/ui-review/r6/wp7/home_1920x1080.png           | Bin 0 -> 198188 bytes
 docs/ui-review/r6/wp7/home_390x844.png             | Bin 0 -> 101619 bytes
 docs/ui-review/r6/wp7/pdp_1366x768.png             | Bin 0 -> 169484 bytes
 docs/ui-review/r6/wp7/pdp_1536x864.png             | Bin 0 -> 175276 bytes
 docs/ui-review/r6/wp7/pdp_1920x1080.png            | Bin 0 -> 202096 bytes
 docs/ui-review/r6/wp7/pdp_390x844.png              | Bin 0 -> 87231 bytes
 docs/ui-review/r6_defects.md                       |  37 +
 frontend/css/components/cards.css                  |  13 +-
 frontend/css/components/cart.css                   |   6 +-
 frontend/css/components/editorial-cutout.css       |  18 +-
 frontend/css/components/editorial-hero.css         |  39 +-
 frontend/css/components/editorial-plate.css        |  50 +-
 frontend/css/components/editorial-spread.css       | 135 +++
 frontend/css/components/footer.css                 |  10 +-
 frontend/css/components/header.css                 | 219 ++++-
 frontend/css/components/media-slot.css             |   4 +-
 frontend/css/layout-editorial.css                  | 903 ++++++++++++++++++++-
 frontend/css/layout.css                            |  25 +-
 frontend/css/tokens.css                            |  12 +
 frontend/js/editorial.js                           | 175 ++--
 frontend/js/modules/chapter_transitions.js         |   1 +
 frontend/js/modules/collectible_cards.js           |   2 +-
 frontend/js/modules/header-scroll.js               |  28 +-
 frontend/js/modules/headline_cutouts.js            |  64 +-
 frontend/js/modules/menu-panel.js                  | 128 ++-
 frontend/js/modules/pdp_exhibition.js              | 231 +++++-
 frontend/js/modules/scroller.js                    |   1 +
 scripts/allowlist_audit.py                         | 157 ++++
 scripts/capture_r6_after.py                        | 278 +++++++
 scripts/capture_r6_before.py                       | 168 ++++
 scripts/capture_r6_wp1.py                          |  72 ++
 scripts/capture_r6_wp3.py                          | 124 +++
 scripts/capture_r6_wp4.py                          |  83 ++
 scripts/capture_r6_wp5.py                          |  71 ++
 scripts/capture_r6_wp6.py                          |  98 +++
 scripts/capture_r6_wp7.py                          |  82 ++
 scripts/exercise_admin_e2e.py                      | 318 ++++----
 scripts/exercise_auth_e2e.py                       | 288 ++++---
 scripts/fold_audit.py                              |  12 +-
 scripts/idle_check.py                              | 186 +++++
 scripts/overlap_audit.py                           | 223 +++++
 scripts/perf_audit.py                              | 209 +++++
 scripts/sync_diff_stat.py                          |  26 +
 scripts/test_cdn_fallback.py                       | 132 +++
 static/vendor/gsap/LICENSE.txt                     |  11 +
 static/vendor/gsap/ScrollTrigger.min.js            |  11 +
 static/vendor/gsap/cdn_fallback.js                 |  46 ++
 static/vendor/gsap/gsap.min.js                     |  11 +
 templates/admin/index.html                         |   4 +-
 templates/base.html                                |   5 +
 templates/catalog/category_detail.html             | 155 ++--
 templates/catalog/category_list.html               |   1 -
 templates/catalog/home.html                        | 371 +++++----
 templates/catalog/product_detail.html              | 190 ++++-
 templates/includes/header.html                     | 103 ++-
 templates/includes/mini_bag.html                   |   2 +-
 templates/includes/product_image.html              |  10 +
 templates/includes/stock_badge.html                |  10 +-
 templates/pages/privacy.html                       |  15 +-
 templates/pages/refunds.html                       |  29 +-
 templates/pages/shipping.html                      |   2 +-
 templates/pages/terms.html                         |   4 +-
 tests/js/menu_panel.test.js                        | 162 ++++
 tests/test_catalog_filters.py                      |  64 ++
 tests/test_catalog_services.py                     |  15 +
 tests/test_r6_shop_floor.py                        | 236 ++++++
 328 files changed, 6298 insertions(+), 879 deletions(-)
```

---

## 12. Conclusion & Verification Sign-Off

The **FINAL PASS R6: THE SHOP FLOOR** stands complete, frozen, and verified:
1. **Academic Honesty**: All test outputs, contrast ratios, and layout measurements come from executed scripts. Zero products, ratings, or policies were fabricated.
2. **Quality Gates Passed**: 0 overlap defects, 0 void defects, 0 layout defects, 0 fold defects, 0 idle animations, 0 unauthorized network calls, and 100% offline functionality.
3. **Pacing & Performance**: Homepage height strictly capped at 4,474px ($\le 4,608\text{px}$ gate). Zero long tasks over 100ms during 4x CPU throttled scrolls.
4. **Code Freeze**: No further edits will be made. The storefront is fully prepared for university faculty inspection.
