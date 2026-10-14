# ELECTROCART R4 UI DEFECTS REGISTER (VISUAL TRUTH RESET)

**Baseline Audit Viewports:** Desktop (1456x820) and Mobile (390x844)  
**Inspection Engine:** Playwright Chromium headless with live screenshot analysis  
**Screenshot Archive:** `docs/ui-review/r4/before/`  
**Date:** 2026-10-09  

---

## 1. Defect Register

| ID | Page / Component | Defect Description | Severity | Screenshot Evidence | Status |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **D-01** | Category Marquee (`/c/<slug>/`) | Four marquee picks stack vertically in a narrow ~170px column, leaving a massive ~700px empty void across columns 5–12. | **S0** | `docs/ui-review/r4/before/category_marquee_top_1456.png` | OPEN |
| **D-02** | Category Detail (`/c/<slug>/`) | "All {n} Listings" divider placed inside marquee section with a 414px gap before `.catalog-layout` grid, causing the grid area under the divider to render completely blank on initial scroll. | **S0** | `docs/ui-review/r4/before/category_marquee_grid_1456.png`<br>`docs/ui-review/r4/before/category_marquee_grid_390.png` | OPEN |
| **D-03** | Category & Index Headings | "Earphones & Headphones" and "Smartphones & Devices" titles wrap onto 3 lines with an orphaned "&" stranded on its own line. | **S1** | `docs/ui-review/r4/before/category_marquee_top_1456.png`<br>`docs/ui-review/r4/before/categories_1456.png` | OPEN |
| **D-04** | Category Marquee Microcopy | Chapter label reads "01 Category Overview" instead of plain "Chapter 01". Marginalia says "Curated listings" instead of "Listings". Duplicate range line appears under headline and in marginalia. | **S1** | `docs/ui-review/r4/before/category_marquee_top_1456.png` | OPEN |
| **D-05** | Rupee Number Formatting | Unformatted rupee figures without commas (e.g. `₹20499` instead of `₹20,499`) present on category and index headers. | **S1** | `docs/ui-review/r4/before/category_marquee_top_1456.png`<br>`docs/ui-review/r4/before/categories_1456.png` | OPEN |
| **D-06** | Product Plates (F-13) | Product photos sit in a visible lighter/white box on tinted plate mats; `mix-blend-mode: multiply` fails to dissolve white backgrounds seamlessly into surface colors. | **S1** | `docs/ui-review/r4/before/category_marquee_top_1456.png`<br>`docs/ui-review/r4/before/home_chapter_01_earphones-headphones_1456.png` | OPEN |
| **D-07** | Product Cards | Brand displayed in all-caps (e.g. "BOAT") directly above title starting with brand name ("boAt BassHeads..."). Captions show bare single-word color values ("Black", "Red") instead of validated technical specs. | **S1** | `docs/ui-review/r4/before/category_marquee_top_1456.png`<br>`docs/ui-review/r4/before/category_marquee_top_390.png` | OPEN |
| **D-08** | Header & Iconography | "Shop" dropdown chevron is a stray jagged curve. Heart/wishlist icon outline clipped at high zoom and collides with Shop dropdown on 390px mobile viewports. | **S1** | `docs/ui-review/r4/before/home_top_1456.png`<br>`docs/ui-review/r4/before/home_top_390.png` | OPEN |
| **D-09** | Hero Headline Cutouts | Punctuation floats awkwardly with leading spaces (`plug in [img] ,`), and cutout images display square white borders. Hero subtitle listing count `6706` lacks thousand separator. | **S2** | `docs/ui-review/r4/before/home_top_1456.png` | OPEN |
| **D-10** | Chapter Layout & Pinned Stage | Home chapters currently render as unpinned stacks with mismatched heights between lead plate and 2-stack cards; chapter title scrolls underneath sticky header without `scroll-padding-top` clearance. | **S1** | `docs/ui-review/r4/before/home_chapter_01_earphones-headphones_1456.png`<br>`docs/ui-review/r4/before/home_chapter_02_smartphones_1456.png` | OPEN |
| **D-11** | Editorial Story Sections | "How buying works", "The brands", and footer colophon separated by dead empty vertical voids exceeding 200px–300px. | **S1** | `docs/ui-review/r4/before/home_buying_1456.png`<br>`docs/ui-review/r4/before/home_brands_1456.png`<br>`docs/ui-review/r4/before/home_footer_1456.png` | OPEN |
| **D-12** | Categories Index Gallery | `/categories/` currently renders as a flat vertical list on desktop; missing Tier 1 pinned horizontal gallery walk per specification. | **S1** | `docs/ui-review/r4/before/categories_1456.png` | OPEN |
| **D-13** | Product Detail Animation & Media | PDP lacks exhibition-frame reveal choreography (clip-path open, photo settle, spec rule-draw). Reusable video and 3D media slots are absent. | **S1** | `docs/ui-review/r4/before/pdp_instock_1456.png`<br>`docs/ui-review/r4/before/pdp_unpriced_1456.png` | OPEN |
| **D-14** | Cart & Checkout Microcopy | Shipping meter threshold displays decimal paise (`₹499.00`) inconsistent with whole-rupee styling. Order placement flash message contains an exclamation mark violating copy honesty rules. | **S1** | `docs/ui-review/r4/before/cart_filled_1456.png`<br>`docs/ui-review/r4/before/order_success_1456.png` | OPEN |
| **D-15** | Owner Story Text Hooks | Missing optional `Category.chapter_intro` admin narrative field for owner-written editorial storytelling. | **S1** | Schema inspection | OPEN |

---

## 2. Methodology & Verification Contract

Every defect listed above was verified via real browser screenshots. A defect is only marked **FIXED** when:
1. The code change is implemented at the root cause.
2. A matching screenshot is captured at the identical viewport and scroll position in `docs/ui-review/r4/after/`.
3. The before and after screenshots are visually compared and described.
4. Deterministic audit scripts (`scripts/void_audit.py`, `scripts/layout_audit.py`, `scripts/full_qa.py`) confirm zero empty rectangles > 600x300px and zero stuck hidden elements.
