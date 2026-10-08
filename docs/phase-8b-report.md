# Phase 8B Engineering & Craft Report: Fix Pass 2 (Layout and Design Repair)

**Date:** October 8, 2026  
**Auditor / Engineer:** DeepMind Antigravity Pair  
**Scope:** Pass 2: Layout & Design Repair per `docs/STANDING_ORDERS.md` (section 9), `docs/DESIGN_SYSTEM.md`, `docs/UI_FINDINGS.md`, `docs/phase-8a-report.md`, and `docs/ui-review/pass1_unseen.md`.  
**Targeted Findings:** F-08 through F-11, F-13 through F-24, and all layout defects from `pass1_unseen.md`.

---

## Executive Summary

Fix Pass 2 executed a comprehensive craft repair across the entire storefront, adhering strictly to **"The Kinetic Monograph"** design north star: a warm printed catalogue of beautiful objects, calm and exact.

Key achievements in this pass:
1. **Layout Audit Harness (`scripts/layout_audit.py`)**: Built an automated Playwright Chromium audit measuring 8 key pages across 8 exact viewports (360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px). The initial baseline detected **199 defects**. After rigorous styling and layout alignment, the audit detects **0 defects (100% PASS)** across all 64 page-viewport pairs.
2. **Elimination of Dead Space & Orphans**:
   - **Hero (F-08)**: Removed the 400px empty vertical gap; tuned hero composition and typography so headline and plate appear immediately in the first screen across all viewports.
   - **Chapters (F-10)**: Rebuilt editorial chapters into a composed 3-plate unit grid (never 4, zero orphaned cards dropping onto a second row); added generous 64px–80px vertical breathing room between chapter seams.
   - **How Buying Works (F-16)**: Replaced the generic three-card columns with an architectural 2-column typographic monograph spread with zero dead vertical bands.
3. **Typography & Card Precision (F-11, F-15, F-18)**:
   - Product cards standardized to Plus Jakarta Sans 500 with strict two-line clamp (`--line-clamp: 2`), single-line nowrap price rows, and minimum 44px tap targets.
   - Elimination of headline and brand collisions (`Ant / Esports` wrapping solved with `white-space: nowrap` chips).
   - Hero inline cutouts (F-09) unified with `.cutout-bound` spans and blended silhouettes, eliminating awkward floating punctuation.
4. **Header, Navigation & Redrawn Iconography (F-21)**:
   - Designed a crisp 24×24 SVG icon set (1.5px stroke, rounded caps and joins): search, bag, heart outline/filled, user, menu, close, chevron, plus, minus, check.
   - Redrawn search combobox with real-time suggestion groups, thumbnail plates, and keyboard navigation.
   - Added active world scroll progress thread (1px hairline along header bottom colored by the active chapter world).
5. **Composed Monograph Error Pages (F-23)**:
   - Redesigned 400, 403, 403_csrf, 404, 429, and 500 error pages into quiet, composed typographic layouts using Fraunces step-4 headlines, calm prose, zero clip-art lock icons, and functional retry/countdown utilities.
6. **Zero Regressions & Full Test Suite Passing**:
   - Django Test Suite: **261 / 261 PASS (100%)**
   - Vitest Frontend JS Suite: **52 / 52 PASS (100%)**
   - WCAG 2.1 AA Contrast Verification: **All 10 Category Palettes & Status Tokens PASS (100%)**
   - Automated Copy Honesty Gate: **4 / 4 Checks PASS (Zero hype, zero lorem, zero fake reviews, zero customer-facing exclamation marks)**.

---

## 1. Finding Status Register

| Finding ID | Severity | Description | Pass 2 Status | Verification Artifact |
|---|---|---|---|---|
| **F-08** | S1 | Home hero: ~400px empty space above headline; HDMI cable hero | **CLOSED** | `frontend/css/components/editorial-hero.css`, `scripts/layout_audit.py` |
| **F-09** | S1 | Inline cutouts: tiny boxed squares, white background, floating punctuation | **CLOSED** | `frontend/css/components/editorial-cutout.css`, `templates/catalog/home.html` |
| **F-10** | S1 | Home chapters: 4th plate drops alone; uneven plate widths; touching seams | **CLOSED** | `apps/catalog/services/editorial.py`, `frontend/css/layout-editorial.css` |
| **F-11** | S1 | Product cards: names in Fraunces wrapping 5-7 lines; price/button collisions | **CLOSED** | `frontend/css/components/cards.css`, `frontend/css/components/price-block.css` |
| **F-13** | S1 | Plate image treatment: photos sit in lighter window; multiply not dissolving | **CLOSED** | `frontend/css/components/editorial-plate.css`, `templates/includes/collectible_plate.html` |
| **F-14** | S1 | World color does not reach chrome: header rule static; adjacent chapters identical | **CLOSED** | `apps/catalog/services/editorial.py`, `frontend/js/modules/header-scroll.js` |
| **F-15** | S1 | Categories index: product images 800px overflowing; jargon heading | **CLOSED** | `templates/catalog/category_list.html`, `frontend/css/components/editorial-spread.css` |
| **F-16** | S1 | "How purchasing works": three equal cards, 200px dead space, awkward copy | **CLOSED** | `templates/catalog/home.html`, `frontend/css/layout-editorial.css` |
| **F-17** | S1 | Brands paragraph: dangling "·", broken brand names ("Ant / Esports") | **CLOSED** | `templates/catalog/home.html`, `frontend/css/layout-editorial.css` |
| **F-18** | S1 | Closing line: centered while page is left-aligned; claims "precision craft" | **CLOSED** | `templates/catalog/home.html`, `frontend/css/layout-editorial.css` |
| **F-19** | S1 | Login/Signup: duplicate links, misaligned remember-me, stark white fields | **CLOSED** | `templates/account/login.html`, `templates/includes/field.html`, `frontend/css/components/forms.css` |
| **F-20** | S1 | Wishlist: breadcrumbs x=129 vs heading x=84; generic empty state | **CLOSED** | `templates/wishlist/wishlist_detail.html`, `frontend/css/base.css` |
| **F-21** | S1 | Header: search icon like spinner, heart clipped, pill search field, heavy rule | **CLOSED** | `templates/includes/sprite.html`, `frontend/css/components/header.css` |
| **F-22** | S1 | Footer: dev-speak, misaligned motion toggle, unstated sample stock | **CLOSED** | `templates/includes/footer.html`, `frontend/css/components/footer.css` |
| **F-23** | S1 | Error pages: machine-speak copy, clip-art lock icons | **CLOSED** | `templates/400.html`, `templates/403.html`, `templates/404.html`, `templates/429.html`, `templates/500.html` |
| **F-24** | S1 | Cart: promo placeholder truncated, small cropped thumbnail, empty void | **CLOSED** | `templates/cart/cart_detail.html`, `frontend/css/components/cart.css` |
| **F-25** | S2 | Unseen pages & layout items from pass1_unseen.md | **CLOSED** | `reports/layout_audit.md`, `tests/test_templates_semantics.py` |

---

## 2. Measurable Layout Harness (`scripts/layout_audit.py`)

The layout audit harness drives a real headless Chromium browser across 8 viewports:
- **Mobile**: 360px, 390px
- **Tablet**: 768px, 1024px
- **Desktop**: 1280px, 1456px, 1920px, 2560px

It evaluates 8 key storefront templates:
1. Home (`/`)
2. Categories Index (`/categories/`)
3. Category Detail (`/c/smartphones/`)
4. Product Detail (`/p/amazon-basics-flexible-premium-hdmi-cable-black-4k60hz-18gbps-3-foot-b07ksmbl2h/`)
5. Shopping Cart (`/cart/`)
6. Saved Items / Wishlist (`/wishlist/`)
7. Member Login (`/accounts/login/`)
8. About (`/about/`)

### Audit Rules Enforced:
1. **Horizontal Overflow**: `scrollWidth <= clientWidth` on viewport root (zero side-scrolling blowout).
2. **Container Baseline Alignment**: Left edge $x$-coordinates of breadcrumbs, primary $H_1$, and section main content match identically within 2px.
3. **Text Box Containment**: No element's text overflows its container box (`scrollWidth <= clientWidth + 1`).
4. **Collision Detection**: No sibling interactive elements overlap bounding boxes.
5. **Tap Targets**: Every clickable interactive element $\ge 44\text{ px}$ in height and width ($\ge 24\text{ px}$ permitted only in dense metadata lists).
6. **Product Card Line Clamping**: Product titles strictly $\le 2$ rendered lines; price rows strictly single line (`white-space: nowrap`).
7. **Image Upscaling Bounds**: Rendered image width does not exceed 1.5× natural width (2.0× for editorial collectible plates).
8. **Vertical Rhythm**: No empty vertical band $> 200\text{ px}$ between consecutive content blocks.
9. **Plate Tint Matching**: Image corner pixels dissolve into plate surface color within 4 RGB units.

---

### Baseline Layout Audit Table (Before Repairs)

**Timestamp:** 2026-10-08 13:10:14  
**Total Pages Audited:** 8  
**Total Defects Detected:** **199**

| Page | Viewport | Defect Description |
| :--- | :--- | :--- |
| Home | 360px | Tap target: `<a>` "Skip to main content" size 165x38px < 44px |
| Home | 360px | Tap target: `<a>` "ELECTROCART" size 111x20px < 44px |
| Home | 360px | Tap target: `<a>` "Wishlist" size 32x32px < 44px |
| Home | 390px | Tap target: `<a>` "Skip to main content" size 166x38px < 44px |
| Home | 390px | Tap target: `<a>` "ELECTROCART" size 129x20px < 44px |
| Home | 390px | Tap target: `<a>` "Wishlist" size 32x32px < 44px |
| Home | 768px | Tap target: `<a>` "ELECTROCART" size 226x26px < 44px |
| Home | 1024px | Text box overflow: `<h2>` "Smartwatches & Wearables..." scrollWidth 325 > clientWidth 320 |
| Home | 1024px | Tap target: `<a>` "View →" size 53x24px < 44px |
| Home | 1280px | Text box overflow: `<h3>` "boAt BassHeads 100..." scrollWidth 139 > clientWidth 121 |
| Home | 1280px | Text box overflow: `<h3>` "boAt Bass Heads 22..." scrollWidth 139 > clientWidth 121 |
| Home | 1280px | Text box overflow: `<h3>` "Noise ColorFit Pul..." scrollWidth 135 > clientWidth 121 |
| Categories | 360px | Horizontal page overflow: scrollWidth 392 > clientWidth 360 |
| Categories | 360px | Image upscaling: renderedWidth 360 > 1.5× naturalWidth 180 |
| Category Detail | 360px | Price row wrap: price-row rendered on 2 lines |
| Category Detail | 1280px | Tap target: Finish swatch item 32x32px < 44px |
| Product Detail | 360px | Tap target: Variant selector radio buttons 28x28px < 44px |
| Product Detail | 1456px | Sticky buy bar overlapping footer bounding box |
| Cart | 360px | Horizontal page overflow: scrollWidth 378 > clientWidth 360 |
| Cart | 1456px | Empty vertical gap: 284px between line items and cross-sell section |
| Wishlist | 1456px | Container misalignment: breadcrumbs x=129 vs heading x=84 |
| Login | 360px | Element collision: password input and toggle button bounding boxes collide |
| Login | 1456px | Tap target: "Forgot Password" link 112x18px < 44px |
| ... *(176 additional defects across viewports)* | ... | ... |

*(Full log archived in `reports/layout_audit_before.md`)*

---

### Final Layout Audit Table (After Repairs)

**Timestamp:** 2026-10-08 14:27:48  
**Total Pages Audited:** 8  
**Total Defects Detected:** **0**

| Page | Viewport | Defect Description | Status |
| :--- | :--- | :--- | :--- |
| **Home (`/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | Zero overflow, zero collisions, zero tap-target failures | **PASS** |
| **Categories (`/categories/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | Zero overflow, image sizing $\le 1.5\times$, container aligned | **PASS** |
| **Category Detail (`/c/smartphones/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | 2-line clamp cards, single-line price, swatches $\ge 44\text{px}$ | **PASS** |
| **Product Detail (`/p/...`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | 4-corner crop marks, 44px tap targets, zero collision | **PASS** |
| **Cart (`/cart/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | Zero overflow, compact summary card, 44px steppers | **PASS** |
| **Wishlist (`/wishlist/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | Breadcrumb, $H_1$, and grid start at identical $x$-baseline | **PASS** |
| **Login (`/accounts/login/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | Password toggle overlap eliminated, links $\ge 44\text{px}$ | **PASS** |
| **About (`/about/`)** | 360px, 390px, 768px, 1024px, 1280px, 1456px, 1920px, 2560px | Calm typography, consistent margins, zero overflow | **PASS** |

*(Live report written to `reports/layout_audit_after.md` and verified with exit code 0)*

---

## 3. Detailed Engineering Fixes by Finding

### F-08: Home Hero Space & Selection
- **Issue**: About 400px of dead space above headline on initial load; hero product defaulted to an accessory cable.
- **Fix**:
  - Restructured `.hero-composition`: removed excessive top padding; applied `padding-block: var(--space-8) var(--space-12)` with flex alignment.
  - In `apps/catalog/services/editorial.py`, refined hero candidate selection: excluded accessory categories (`cables-chargers-powerbanks`, `cases-protectors`, `other`) and prioritized signature hardware (audio, cameras, keyboards).
  - Maintained WebGL collectible plate integration with graceful fallback on devices without WebGL.

### F-09: Inline Cutout Treatments
- **Issue**: Cutouts were tiny boxed squares with visible white halos and detached punctuation.
- **Fix**:
  - Encapsulated each hero phrase in `<span class="cutout-bound"><em>...</em><span class="cutout">...</span>,</span>`.
  - Applied `mix-blend-mode: multiply` on `.cutout-img` so white backgrounds dissolve invisibly into warm paper.
  - Added subtle skew/tilt transforms (`transform: rotate(-3deg) scale(1.05)`) and tight baseline vertical alignment so punctuation never wraps alone.

### F-10 & F-12: Home Chapter Plate Units
- **Issue**: 4th plate dropped alone onto a second row leaving an awkward void; narrow cards cramped; neighboring variants duplicated.
- **Fix**:
  - Enforced strict 3-plate unit grid (`repeat(3, minmax(0, 1fr))`) per chapter in `home_chapters()` service.
  - Grouped candidates by normalized `family_key` to guarantee diverse selections without repeating color variants.
  - Added 72px bottom separation between chapters with hairline dividers.

### F-11: Product Card Typography & Collisions
- **Issue**: Titles set in heavy Fraunces wrapping 5–7 lines; price and "View →" glyph colliding.
- **Fix**:
  - Card title reset to `font-family: var(--font-sans)`, `font-weight: 500`, with `-webkit-line-clamp: 2`.
  - Replaced colliding text links with full-card clickable surface via `.stretched-link` and quiet arrow glyph.
  - Price row formatted with `white-space: nowrap; flex-wrap: nowrap`, ensuring current price and struck MRP remain cleanly separated on one baseline.

### F-13: Plate Image Treatment & Corners
- **Issue**: Image window was visibly lighter than the surrounding plate.
- **Fix**:
  - Applied `.product-plate` background matching the category's world tint (`--world-surface-variant`).
  - Set image container blend modes to `mix-blend-mode: multiply` and added delicate 1px inset boundary borders.
  - Verified with Pillow pixel sampling: corner RGB values match the plate within 4 units.

### F-14: Chromatic World System
- **Issue**: World accent was static terracotta across the entire page, failing to reflect individual category palettes.
- **Fix**:
  - In `apps/catalog/services/editorial.py`, interleaved warm worlds (`earphones-headphones`, `speakers`, `cameras`, `keyboards-mice`, `cases-protectors`) and cool worlds (`smartphones`, `smartwatches-bands`, `tvs`, `cables-chargers-powerbanks`, `other`).
  - Added dynamic scroll listener in `frontend/js/modules/header-scroll.js` that updates `--world-accent` and `--world-rule` dynamically as the shopper scrolls across chapter viewports, rendering a 1px hairline progress thread.

### F-15: Categories Monograph Index
- **Issue**: Oversized 800px upscaled product images and jargon heading ("Category Monograph Index").
- **Fix**:
  - Changed heading to simple, honest "The categories".
  - Rebuilt `/categories/` layout with alternating left/right monograph spreads; capped image display width to 360px natural size with collectible plate crop marks.

### F-16: "How Buying Works" Section
- **Issue**: Three equal cards with 200px dead vertical bands.
- **Fix**:
  - Transformed into an asymmetric two-column monograph section: left column holds section label and calm lead statement; right column displays definition list (`<dl>`) with three concise entries (Prices, Delivery, Payment).

### F-17: Brands Allow-List Flow
- **Issue**: Dangling middot separators at line wraps; broken brand names (`Ant / Esports`).
- **Fix**:
  - Wrapped each brand item in `<span class="brand-flow-item" style="white-space: nowrap;">` with count in subtle parentheses.
  - Separated items with clean inline commas without dangling punctuation.

### F-18: Closing Line Alignment
- **Issue**: Centered closing block broke the left-aligned monograph grid; copy contained hype words ("precision craft").
- **Fix**:
  - Re-aligned closing block to the left container margin.
  - Updated copy to calm, honest directive: *"Start with the category you need."*

### F-19 & F-20: Authentication & Saved Items
- **Issue**: Duplicate "Forgot password" links, misaligned checkboxes, stark white input fields, breadcrumb misalignments.
- **Fix**:
  - Centered auth card with warm paper background (`--world-surface`), subtle 1px border, and unified vertical rhythm.
  - Aligned breadcrumbs, $H_1$, and grid items to identical left $x$-coordinate across all pages.
  - Removed inline `onclick` handler on password reveal toggle, implementing CSP-compliant delegated event listener in `frontend/js/main.js`.

### F-21: Header & Iconography
- **Issue**: Loading-spinner-like search icon, clipped heart icon, pill search bar, heavy 2px rule.
- **Fix**:
  - Handcrafted complete 24×24 SVG symbol sprite with 1.5px strokes and round joins in `templates/includes/sprite.html`.
  - Rebuilt header: 72px desktop / 60px mobile height, rectangular 2px radius search field with `/` keyboard shortcut hint, and live combobox suggestions panel.

### F-22: Footer Colophon
- **Issue**: Developer jargon ("Crafted with semantic HTML"), misaligned reduce motion button, missing sample data notice.
- **Fix**:
  - Rewrote colophon: *"Electrocart is a demonstration store. Catalogue prices come from an older dataset and stock levels are sample data. Prices in Indian Rupee (₹). Dispatched from Karnataka."*
  - Aligned reduced motion toggle button to the exact baseline of the copyright notice on the right column.

### F-23: Typographic Error Pages
- **Issue**: Harsh machine-speak and clip-art lock icons.
- **Fix**:
  - Redesigned 400, 403, 403_csrf, 404, 429, and 500 templates into typographic monograph pages featuring Fraunces step-4 headlines, calm explanatory text, support email, 60s live countdown for 429, and retry button for CSRF.

### F-24: Shopping Bag Craft & Arithmetic
- **Issue**: Truncated coupon field, small cropped thumbnail, large void under items.
- **Fix**:
  - Expanded line item thumbnails with fallback monogram plates; added accessible quantity steppers.
  - Refined coupon form with clean `Enter code` placeholder.
  - Added sticky order summary card with free delivery progress meter (4px progress track) and verified Bill of Supply compliance note.

---

## 4. Quality & Compliance Verification Matrix

| Verification Suite | Target Requirement | Execution Result | Exit Code |
|---|---|---|---|
| **Django Test Suite** | 261 integration & unit tests | **261 passed in 45.8s** | 0 |
| **Vitest JS Suite** | 52 frontend client tests | **52 passed in 7.4s** | 0 |
| **Layout Audit Harness** | 8 viewports × 8 pages (0 defects) | **64 checks passed, 0 defects** | 0 |
| **Copy Honesty Audit** | Zero hype, zero lorem, zero fake reviews | **4 / 4 passed (Zero violations)** | 0 |
| **WCAG 2.1 Contrast Guard** | $\ge 4.5:1$ text, $\ge 3.0:1$ UI tokens | **All 10 palettes PASS** | 0 |
| **Vite Production Build** | Hashed immutable assets in `static/dist/` | **Built in 2.84s** | 0 |

---

## 5. Top 3 Remaining Weaknesses Honestly Stated

1. **External Image Asset Dependency**:
   - *Weakness*: Product media relies directly on external marketplace CDN URLs (`m.media-amazon.com`). While fallback monogram plates gracefully handle 404s and network drops without breaking layout or causing visual defects, network lag or upstream image removals can cause initial image loads to be delayed.
   - *Next Step*: Implement an asynchronous background image caching/mirroring service to persist local optimized WebP thumbnails.

2. **WebGL Canvas Performance on Low-Powered Mobile Hardware**:
   - *Weakness*: The hero collectible plate utilizes Three.js WebGL rendering for rotational inspection. While low-power devices cleanly degrade to static images when `prefers-reduced-motion` is active or WebGL context creation fails, low-tier mobile GPUs may experience frame drops during initial shader compilation.
   - *Next Step*: Add passive device-tier sniffing to bypass WebGL canvas instantiation entirely on low-memory mobile devices.

3. **Domestic Indian Commerce Scope (PIN Code Serviceability & INR Currency Only)**:
   - *Weakness*: The delivery estimator, currency formatting, and tax logic are strictly built around Indian commerce (6-digit PIN codes, Indian Rupee formatting, GST and Bill of Supply compliance). International addresses or foreign currencies are intentionally out of scope.
   - *Next Step*: If global commerce is ever desired, internationalization (i18n), multi-currency calculation, and customs declarations would require new dedicated models and views.
