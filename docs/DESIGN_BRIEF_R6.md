# ELECTROCART Phase R6 Design Brief: The Shop Floor
**Date:** 2026-10-14  
**Author:** Pair Programming Agent & Architectural Review  
**Status:** Approved for Implementation

---

## 1. Vision & Architecture Overview

Phase R6 transforms ELECTROCART into a high-density, calm, gallery-grade electronics department store. We replace sprawling, vertically exhausted pinned stages with compact, editorial monograph shelves, responsive horizontal rails, and a structured mega-menu. The total home page height is constrained to strictly less than 6 viewports on standard desktop displays (1366x768).

---

## 2. Section Architectural Briefs

### 2.1 Header & Mega-Menu (WP4)
- **Problem Solved:** The existing shop dropdown is narrow; category counts collide with titles on desktop; mobile navigation requires excessive scrolling.
- **Pattern Chosen:** A 2-column compact mega-menu (fixed max-height 480px) triggered from "Shop". Left column provides a vertically stacked list of all 10 categories with right-aligned tabular item counts; hovering a category dynamically updates the right preview pane with that category's cutout, "Priced from ₹X", top 5 allowlisted brands, and a direct link to "Under ₹999 / ₹4,999". A sticky header scroll thread (`transform: scaleX(...)`) tracks reading depth in the active category's world accent color. Includes Esc key dismissal, outside click detection, and 160ms ease transition.
- **Rejected Alternatives:**
  - *Full-screen overlay takeover*: Rejected because it disorients the shopper and breaks reading continuity.
  - *Multi-level nested hover flyouts*: Rejected due to awkward mouse diagonals and touch incompatibilities.

### 2.2 Category Page & Shelf (WP5)
- **Problem Solved:** Giant category marquee consumes an entire viewport with empty voids and stacked secondary picks, pushing listings below the fold.
- **Pattern Chosen:** Replace the oversized marquee with a slim, high-density "Most Rated" shelf (6 compact cards with label: "Selected by number of ratings on Amazon"). Category header features scannable chip filters for price brackets and top brands. The catalog grid is 4 columns at 1366px and 5 columns at 1920px with square 1:1 plates where products fill >= 70% of plate width.
- **Rejected Alternatives:**
  - *Infinite scrolling without pagination*: Rejected because it breaks bookmarking, footer access, and URL synchronicity.
  - *Aggressive 2.2:1 horizontal card strips*: Rejected as it violates plate geometry rules and hides product details.

### 2.3 Product Page (PDP) Commerce & Lightbox (WP6)
- **Problem Solved:** Images either stretch or cannot be inspected in detail; long spec lists require extensive manual scrolling; adding to bag lacks spatial feedback.
- **Pattern Chosen:**
  - *Gallery Plinth*: Square sticky plinth (max 480px) with native `<dialog>` lightbox providing click-to-zoom and pan; 2x hover lens when primary image resolution >= 600px.
  - *Sticky Sub-Nav*: IntersectionObserver-powered tab bar linking to Overview, Specifications, In the Box, and Similar Items.
  - *Similar Items Comparison*: Real comparison table showing the 3 nearest-priced items in the same category side-by-side with verified specs.
  - *Fly-to-Bag Interaction*: GSAP Flip / transform animation (400ms) flying a miniature thumbnail into the bag icon, opening a calm `<dialog>` mini-bag confirmation drawer.
- **Rejected Alternatives:**
  - *Heavy external zoom libraries (e.g. ElevateZoom)*: Rejected to avoid third-party script bloat and maintain zero CSP violations.
  - *Modal checkout redirect*: Rejected because shoppers prefer remaining on the product sheet to continue browsing or inspect accessories.

### 2.4 Editorial Home Page Rebuild (< 6 Viewports) (WP3)
- **Problem Solved:** The home page previously stretched to 11,845px (15.42 viewports) due to 10 massive full-bleed pinned chapter stages.
- **Pattern Chosen:**
  1. *Top Hero*: Clean editorial hero headline with transparent multiply-blended cutouts, compact live catalog counter, and a 3-thumbnail interactive hero picker.
  2. *Category Quick Rail*: Smooth horizontal snap rail featuring all 10 categories with bottom world-color fill on hover.
  3. *Featured Chapter Shelves*: 3 curated chapter shelves (max 560px height each) featuring a double-width lead pick and 4-6 compact cards with category world top rule.
  4. *Budget Ladder*: Real price bracket tiles linking to search.
  5. *Total Height Target*: Height strictly <= 4,608px (<= 6 viewports at 1366x768).
- **Rejected Alternatives:**
  - *Retaining pinned Lenis horizontal scroll walk*: Rejected because it causes extreme page elongation and traps the user in forced scroll hijacking.

### 2.5 Motion System & CDN Loader (WP7)
- **Problem Solved:** Need for deterministic external CDN loading with offline resilience and zero CSP security regressions.
- **Pattern Chosen:** Allowed hosts restricted to `cdn.jsdelivr.net` and `cdnjs.cloudflare.com`. Pinned exact versions with computed SHA-384 Subresource Integrity (SRI) hashes. Vendored fallbacks in `static/vendor/` loaded automatically if CDN fails or exceeds a 2500ms timeout.
- **Rejected Alternatives:**
  - *Unpinned CDN script tags*: Rejected due to security risks and audit failure.
  - *Ignoring offline fallback*: Rejected because academic exam mode must function without internet connectivity.
