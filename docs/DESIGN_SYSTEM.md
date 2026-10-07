# ELECTROCART Design System: "The Kinetic Monograph"

## 1. Philosophy & Intent
ELECTROCART is conceived as a physical printed exhibition monograph translated to the digital medium. Unlike typical consumer electronics storefronts that rely on fluorescent shouting, flashing timers, and aggressive promotional badges, ELECTROCART treats electronics with editorial reverence:
- **Warm Paper, Deep Ink**: Tactile backgrounds with subtle warmth (`#FBFBF9`, `#F4F3EF`) paired with deep, measured ink tones (`#111110`, `#2B2B28`).
- **Category Worlds**: Rather than uniform branding across disparate hardware, each category inhabits an individual "monograph world" defined by an authentic hardware finish, specific accent color, and custom editorial personality.
- **Strict Spatial Geometry**: Every layout margin, padding, gap, and dimension adheres strictly to an 8-point / 4-point harmonic grid.
- **Typography as Architecture**: Fluid modular typographic clamp scales that adapt continuously between mobile (390px) and wide desktop (1440px+).

---

## 2. CSS Architecture & Layer Hierarchy
Styles are structured using native CSS `@layer` rules to guarantee specificity isolation without selector wars or `!important` directives:

```css
@layer reset, tokens, base, layout, components, utilities, print;
```

1. **`reset`** (`frontend/css/reset.css`): Modern resilient box-sizing, fluid media, margin/padding normalization, form font inheritance.
2. **`tokens`** (`frontend/css/tokens.css`): Pure CSS Custom Properties for palettes, fluid type, spacing, radii, elevations, motion, and z-indices.
3. **`base`** (`frontend/css/base.css`): HTML element primitives, typography defaults, link states, focus indicators, selection highlights.
4. **`layout`** (`frontend/css/layout.css`): Grid systems, containers, sections, headers, footers, sidebars, responsive breakpoints.
5. **`components`** (`frontend/css/components/*.css`): 17 isolated component stylesheets covering all functional widgets and modules.
6. **`utilities`** (`frontend/css/utilities.css`): Spacing, alignment, flexbox, visibility, and typography utility classes.
7. **`print`** (`frontend/css/print.css`): High-fidelity print styles for invoices, packing slips, order receipts, and physical monographs.

---

## 3. The 10 Frozen Monograph Worlds
Each category slug maps to a dedicated monograph world via the `data-world` attribute on the `<body>` element or container:

| Category Slug | World Accent | Surface / Plate | Contrast (Accent/BG) | WCAG 2.1 AA | Hardware Metaphor |
|:---|:---|:---|:---:|:---:|:---|
| `earphones-headphones` | `#8C531B` (Oxidized Copper) | `#F4EFEA` | 5.47 : 1 | PASS | Anodized copper driver housing & acoustic mesh |
| `speakers` | `#2D5A4C` (Forest Resonance) | `#EDF3F0` | 5.72 : 1 | PASS | Cast aluminum chassis & woven ballistic acoustic cloth |
| `smartphones` | `#8A3D52` (Burgundy Slate) | `#F6EEF1` | 6.63 : 1 | PASS | Matte frosted ceramic glass & surgical-grade steel band |
| `smartwatches-bands` | `#5C4A6F` (Smoky Quartz) | `#F2EEF5` | 6.74 : 1 | PASS | Bead-blasted titanium casing & fluoroelastomer strap |
| `cameras` | `#6E4F32` (Vintage Brass) | `#F5F0EB` | 6.53 : 1 | PASS | Knurled knurled magnesium alloy & vulcanite grip wrap |
| `tvs` | `#1E3F5A` (Deep Indigo) | `#EBF0F5` | 9.89 : 1 | PASS | Micro-edge carbon fiber bezel & OLED true-black substrate |
| `keyboards-mice` | `#3F5C38` (Pine Artisan) | `#EEF3EC` | 7.15 : 1 | PASS | PBT dye-sublimated keycaps & CNC milled 6063 aluminum |
| `cables-chargers-powerbanks` | `#73482F` (Braided Terra) | `#F5EFEA` | 6.47 : 1 | PASS | Paracord braided sleeve & laser-etched GaN heatsink |
| `cases-protectors` | `#6A4D59` (Slate Rose) | `#F4EFF2` | 5.76 : 1 | PASS | Vegetable-tanned leather & tempered aluminosilicate glass |
| `other` | `#4F5960` (Graphite Tool) | `#F0F2F4` | 7.89 : 1 | PASS | Industrial brushed stainless steel & technical polymer |

All 10 category worlds guarantee a minimum of 4.5:1 text contrast and 3.0:1 non-text/graphical contrast against their respective backgrounds and surfaces.

---

## 4. Typography System
ELECTROCART uses a fluid type scale powered by CSS `clamp()`, interpolating smoothly between a 390px mobile viewport and a 1440px desktop viewport:

- **Font Families**:
  - Headings / Editorial: `Georgia, "Times New Roman", Times, serif`
  - Body / Specifications: `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif`
  - Monospace / Serial Numbers / SKUs: `ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace`

- **Fluid Type Scale Tokens**:
  - `--step--2`: `clamp(0.6944rem, 0.68rem + 0.08vw, 0.75rem)` (11px → 12px, micro legal & timestamps)
  - `--step--1`: `clamp(0.8333rem, 0.81rem + 0.13vw, 0.90rem)` (13.3px → 14.4px, captions & badges)
  - `--step-0`: `clamp(1.0000rem, 0.96rem + 0.19vw, 1.125rem)` (16px → 18px, base body copy)
  - `--step-1`: `clamp(1.2000rem, 1.14rem + 0.32vw, 1.406rem)` (19.2px → 22.5px, card titles & h4)
  - `--step-2`: `clamp(1.4400rem, 1.34rem + 0.51vw, 1.758rem)` (23px → 28px, section headers & h3)
  - `--step-3`: `clamp(1.7280rem, 1.58rem + 0.77vw, 2.197rem)` (27.6px → 35px, page titles & h2)
  - `--step-4`: `clamp(2.0736rem, 1.86rem + 1.12vw, 2.747rem)` (33.2px → 44px, display headlines & h1)
  - `--step-5`: `clamp(2.4883rem, 2.18rem + 1.62vw, 3.433rem)` (39.8px → 55px, hero monograph titles)
  - `--step-6`: `clamp(2.9860rem, 2.55rem + 2.30vw, 4.292rem)` (47.8px → 68.7px, jumbo hero displays)
  - `--step-7`: `clamp(3.5832rem, 2.97rem + 3.23vw, 5.365rem)` (57.3px → 85.8px, monumental numerals)

---

## 5. Spacing & Geometric Grid
Spacing adheres strictly to the 4px base increment:
- `--space-1`: 4px (tight grouping, badge padding)
- `--space-2`: 8px (icon margins, input inner padding)
- `--space-3`: 12px (card compact gutters)
- `--space-4`: 16px (standard component padding)
- `--space-6`: 24px (card padding, grid gaps)
- `--space-8`: 32px (section margins, layout splits)
- `--space-12`: 48px (major section spacing)
- `--space-16`: 64px (hero bands, footer spacing)
- `--space-24`: 96px (editorial chapter breaks)

---

## 6. Component System Contracts

### 6.1 Buttons (`.btn`)
- `.btn`: Base touch target of 44px minimum height, inline-flex, center-aligned, focus ring enabled.
- `.btn-primary`: Category-accented background (or deep ink on neutral pages) with high-contrast text.
- `.btn-secondary`: Crisp 1px hairline border (`var(--color-border)`), surface background, ink text.
- `.btn-quiet`: Borderless, ghost button for low-priority mutations like wishlist removal.
- `.btn-sm`: Compact 34px height for product cards and inline actions.

### 6.2 Product Plate & Cards (`.product-card`, `.product-plate`)
- Clean, non-distracting card borders (`1px solid var(--color-border)`), 4px border radius.
- Dedicated image exhibition plate (`.product-plate`) with subtle inset background (`var(--color-surface)`).
- Secondary action buttons (Quick Add, Compare, Wishlist) accessible with complete keyboard focus states.

### 6.3 Forms & Inputs (`.form-group`, `.input-text`, `.input-select`, `.input-checkbox`)
- Explicit `<label>` elements linked via `for`/`id` on 100% of inputs.
- 44px touch targets on text boxes and select controls.
- Distinct focus states: `3px solid var(--color-accent)` with `2px` offset.
- Floating error notices with `role="alert"` and high-contrast red badge styling (`#C82333`).

---

## 7. Accessibility (WCAG 2.1 AA Compliance)
1. **Contrast Ratio**: 100% verified across 70 standard color pairings, status alerts, and focus rings. Zero violations.
2. **Focus Visibility**: Universal `:focus-visible` styling applied across all interactive elements (`outline: 3px solid var(--color-accent); outline-offset: 2px`).
3. **WCAG 2.5.3 (Label in Name)**: Every control with visible text has an accessible name starting with that exact visible text (e.g., `<button aria-label="Compare {{ product.display_name }}">Compare</button>`).
4. **Semantics & Landmarks**: `<header role="banner">`, `<main id="main-content">`, `<footer role="contentinfo">`, `<nav>`, `<aside>` are cleanly structured without duplicated landmarks.
5. **No JavaScript Dependency**: All store functions (Cart manipulation, checkout, coupons, address management, comparison, search) operate completely under JavaScript-disabled environments. Fetch-enhancement is strictly progressive.

---

## 8. Voice & Microcopy Rules
- **"Bag" over "Cart"**: Customer-facing UI consistently uses "Bag" / "Shopping Bag".
- **Tax Notice**: Every price display is accompanied by the statutory notice: *"Inclusive of all taxes"* or *"Prices inclusive of applicable GST"*.
- **Postal Code**: Consistently referenced as *"PIN code"* rather than "Zip code".
- **Currency**: Formatted with the official Indian Rupee symbol `₹` via the custom `|inr` filter.

---

## 9. Editorial Layer: "The Kinetic Monograph" Patterns

Phase 5 introduced the cinematic editorial layer built on top of the Phase 4 utility system:

### 9.1 Technique H: The Collectible Plate (`.plate-collectible`)
- **Structure**: Outer card container (`.plate-collectible`), inner recessed mat (`.plate-mat`), isolated product image (`.plate-mat-img`), meta line (`.plate-meta-line`), editorial title (`.plate-title`), and footer (`.plate-footer`).
- **Surface Treatment**: The inner mat uses `var(--world-bg)` within a `var(--world-surface)` plate, producing a physical bevel effect. Images use `mix-blend-mode: multiply` on pure white Amazon marketplace assets, rendering them seamlessly into the tinted world paper.
- **Physical Feedback**: Subtle lift on hover (`transform: translateY(-2px)` and `box-shadow: var(--lift-2)`). On desktop devices with pointer precision, dynamic tilt response via `data-tilt-card`.

### 9.2 Technique A: Inline Headline Cutouts (`.cutout`)
- **Structure**: Inline badge container (`.cutout`) with child image (`.cutout-img`) embedded directly inside display typography headlines.
- **Styling**: `height: 0.85em; aspect-ratio: 1 / 1; border-radius: var(--radius-1); transform: skew(-6deg);` with `mix-blend-mode: multiply`.
- **Accessibility Contract**: Always marked with `aria-hidden="true"` and `alt=""` so assistive screen readers read the headline text naturally without decorative image interruptions.

### 9.3 6-Column Asymmetric Grid & Spreads
- **Grid Architecture** (`.grid-editorial-6`): Asymmetric desktop proportions (`1.6fr 1fr 1.2fr 1fr 1.4fr 1fr`) inspired by biennial print catalogues.
- **Chapter Spread** (`.spread`): Full-bleed section with contextual `data-world` tint, hairline top transition seam, and 2-column asymmetric split (`.chapter-grid`).
- **Marginalia Column** (`.marginalia`): Vertical data strip displaying real computed stats (listing count, model count, allow-listed brand count, and live price range) with hairline separators.
- **Chapter Label** (`.chapter-label`): Two-digit romanized numeral (`01`), hairline stroke, and tracking label.

### 9.4 Gallery-Monograph Product Sheet
- **Exhibition Frame** (`.product-sheet-sticky-frame`): Left sticky column housing the primary product plate (`.product-frame-plate`), generous inner mat, and caption strip with technical summary.
- **Finish Swatches** (`.finish-swatch-list`): Circular color-coded hardware chips (`.finish-swatch-circle`) mapped to real electronics finishes (e.g. Space Black, Midnight, Chalk, Sage) via `colour_map.py` and `|colour_hex`.
- **Secondary Media Slot**: Cleanly omitted unless genuine video or 3D plinth models are attached to the product record. Zero fake 3D canvases or empty frames.

