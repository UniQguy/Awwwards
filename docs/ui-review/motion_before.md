# Motion Baseline Verification Register (WP0: Before Repairs)

**Audit Date:** 2026-10-08 14:36:48  
**Harness:** Playwright Headless Chromium at Desktop Viewport (1456×900)  
**Frame Sequences Captured:** `docs/ui-review/frames/hero/` (15 frames) & `docs/ui-review/frames/seam/` (15 frames)

---

## 1. Matrix by Motion Condition

| Feature / Metric | Tier 1 (`?motion=1`) | Tier 2 (`?motion=2`) | Tier 3 (`?motion=3`) | Reduced Motion |
| :--- | :--- | :--- | :--- | :--- |
| **`html[data-motion-tier]`** | `1` | `2` | `3` | `3` |
| **Hero WebGL Canvas** | `True` | `False` | `False` | `False` |
| **Lenis on Home (`/`)** | `True` | `False` | `False` | `False` |
| **Lenis on Cart (`/cart/`)** | `False` | `False` | `False` | `False` |
| **`.chapter-wipe` in DOM** | `0` | `0` | `0` | `0` |
| **Header World Initial** | `` | `` | `` | `` |
| **Header World Scrolled** | `other` | `other` | `other` | `other` |
| **Card Tilt (`data-tilt-card`)** | `{'found': True, 'transform': ''}` | `{'found': True, 'transform': ''}` | `{'found': True, 'transform': ''}` | `{'found': True, 'transform': ''}` |
| **Hero Cutout Data Count** | `10` items | `10` items | `10` items | `10` items |
| **Console Errors / CSP** | `0 errors` | `0 errors` | `0 errors` | `0 errors` |

---

## 2. Key WP0 Findings & Defects Identified

1. **Chapter Diagonal Wipe Defect (Dead Code / Missing Element)**:
   - `chapter_transitions.js` attaches listeners to `.chapter-wipe`, but `templates/catalog/home.html` contained **0 instances of `.chapter-wipe`** (found count: `0`).
   - As a result, the diagonal wipe never fired at chapter seams. Needs markup insertion and verified GSAP ScrollTrigger / CSS clip-path animation.

2. **World Color Propagation to Header**:
   - `header-scroll.js` observes `[data-world]` and updates `header[data-world]` and `--world-accent` on the `#header-progress-thread`.
   - Verified active during scroll: transitioned from `` to `other`.

3. **Lenis Scroller Scope Enforcement**:
   - Lenis initializes on editorial homepage in Tier 1 (`True`), but is strictly absent on `/cart/` (`False`).
   - In Tier 2 and Tier 3 / Reduced Motion, Lenis is completely uninitialized (native scrolling).

4. **Hero WebGL Dynamic Loading**:
   - In Tier 1, WebGL canvas initializes (`True`).
   - In Tier 2 and Tier 3 / Reduced Motion, the WebGL module is honestly skipped, avoiding the Three.js network payload.

5. **Card 3D Perspective Tilt**:
   - `collectible_cards.js` targets `[data-tilt-card]`. On Tier 1 with fine pointer, transforms run upon pointer interaction.

6. **Cutouts Cycling**:
   - `hero-cutouts-data` JSON provides candidate products (`10`).
