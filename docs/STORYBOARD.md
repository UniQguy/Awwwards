# ELECTROCART Storyboard: The Kinetic Monograph

**Catalogue Concept:** A walk through a printed catalogue in six acts.  
**North Star:** A warm printed catalogue of beautiful objects, calm and exact.  
**Rule of Motion:** Motion explains structure, rewards attention, and never gates content. Every effect has a stated architectural reason.  
**Constraint:** Animates *strictly* `transform`, `opacity`, and `clip-path`. Zero layout thrashing. Force-cleared after 2.5 seconds. Disabled under Tier 2/3, mobile, reduced motion, and No-JS.

---

## Act Breakdown

| Act | Name | Storefront Component | Data Displayed | Tier 1 Motion (Fine Pointer Desktop) | Motion Purpose | Tier 2/3, Touch & Reduced Motion Fallback |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Act 1** | **The Cover** | Hero Exhibition Section (`.editorial-hero`) | Headline *"Everything you plug in, put on, or listen with."*, inline collectible cutouts, lead collectible plate, verified catalog count, browse CTA. | **Entrance:** Line-mask reveal (650ms, 90ms stagger) -> cutouts scale from 0.85 & fade (320ms) -> plate lifts 24px with specular sweep.<br>**Scroll Depth:** Headline lines, cutouts, and plate travel at three gentle differential rates (max 40px total). | Establishes the printed monograph format; gives physical depth to paper typography and hardware. | Instant opacity/transform reset. Pure CSS vertical layout. No parallax. |
| **Act 2** | **The Contents** | Typographic Category Table of Contents (`.editorial-index`) | 10 monograph categories, live model counts, price minimums, category accent swatches. | **Rule-draw:** 1px hairline rules draw left-to-right on entry.<br>**Counter roll:** Numeric counts count up once (0 to real value over 600ms).<br>**Hover/Focus:** Category hardware cutout slides into inline badge (180ms). | Explains catalog scope and organization at a glance before deep diving into chapters. | Static rules and values rendered in DOM from the start. Cutout badge appears without slide. |
| **Act 3** | **The Chapters** | Featured Category Spreads (`.chapter-spread` x6) | Category name, honest stats (distinct models, price range), 3 curated/auto picks on collectible plates. | **Pinned Stage:** Left text column pins for ~2.2 viewport heights while the 3 plates enter sequentially on the right (translateY 30px to 0 + fade, 75ms stagger).<br>**Seam:** Diagonal wipe transition hands off to the next monograph chapter world. | Allows the shopper to inspect each chapter's signature objects without losing category context. | **Unpinned composed layout**: Lead plate + 2-stack cards in static 12-column grid. Zero pin, zero scrub. |
| **Act 4** | **How Buying Works** | Transparent Commercial Terms (`.how-buying-section`) | Honest pricing policies (net/GST), delivery rules & threshold (₹499), payment methods (COD/online). | **Sticky Anchor:** Italic summary sentence stays pinned on left while the 3 policy passages reveal with sequenced hairline draws. | Reassures the buyer of clear, honest terms without hype or hidden conditions. | Static 2-column layout; text and hairlines render immediately. |
| **Act 5** | **The Brands** | Allow-Listed Brands Directory (`.brands-flow-section`) | Top 40 allow-listed brand names with genuine item counts. | **Staggered Entry:** Brand chips fade up in a single gentle stagger (30ms per chip). **NO looping marquee.** | Surfaces manufacturer variety cleanly as a printed directory. | Static flex-wrap cloud; no animation. |
| **Act 6** | **The Colophon** | Storefront Footer (`.site-footer`) | Statutory dealer declaration (Bill of Supply / Composition), PIN coverage, legal links, colophon line mask. | **Line-mask:** Footer wordmark reveals smoothly through horizontal line mask once scrolled into view. | Concludes the printed catalogue with formal publication metadata. | Immediate visibility; static layout. |

---

## Category Index Gallery Walk (`/categories/`)

- **Tier 1 Desktop Mode:** Pinned horizontal gallery walk. Vertical page scroll maps to horizontal translation (`xPercent`) across the 10 category monograph spreads.
- **Progress Anchor:** Visible progress hairline at the top with tabular numeral indicator (`01 / 10` through `10 / 10`).
- **Focus & Accessibility Guard:** Keyboard `Tab` navigation immediately scrolls the target spread into viewport view. DOM remains in natural reading order.
- **Fallback (Tier 2/3, Mobile, Reduced Motion, No-JS):** Clean vertical monograph list alternating left and right offset grids.

---

## Category Marquee (`/c/<slug>/`)

- **Composition:** 12-column grid. Columns 1–4 contain the category title (with non-breaking ampersand), optional owner `chapter_intro`, and marginalia statistics. Columns 6–12 contain the composed plates unit (1 large lead plate + up to 3 compact plates with thumbnail mats and tabular prices, bottoms strictly aligned).
- **Motion Vocabulary:** Headline mask reveal, sequenced plate lift-and-fade, hairline draw.
- **Divider Placement:** "All {n} Listings" divider cleanly introduces the browse grid below the marquee, eliminating all empty vertical voids.

---

## Product Exhibition Frame (`/p/<slug>/`)

- **Entrance:** Exhibition plate mat expands from center via `clip-path` (450ms). Product photo scales from `1.04` to `1.00` as it settles into place.
- **Technical Drawing:** Spec summary rows rule-draw sequentially from left edge. Price numerals fade in last.
- **Fine Pointer Parallax:** Gentle $\le 6$px pointer translation on the collectible plate under fine pointer devices.
- **Media Plinth:** Secondary video and 3D glb viewer slots rest under the frame without shifting page layout.

---

## Architectural Rejection Register (Explicitly Not Built)

Per the Design System and Motion Constitution, the following patterns are prohibited:
1. **Custom Cursors / Magnetic Buttons:** Distracts from product content and harms assistive pointer precision.
2. **Looping Marquee Text / Tickers:** Breaks reading pace, causes distraction, and fails WCAG 2.2.2.
3. **Parallax on Utility Views:** Search, Cart, Account, and Checkout remain 100% utilitarian and immediate.
4. **Scroll-jacking on General Pages:** Only the two specified pinned stages exist (Act 3 Chapters and Act 2 Categories walk), both preserving natural scroll momentum and instant keyboard override.
5. **Particle / Canvas Noise:** Degrades battery life and clutters typographic hierarchy.
6. **Autoplaying Audio:** Strictly prohibited. All media slots are muted with no audio tracks required.
