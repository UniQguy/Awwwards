# ELECTROCART Motion & Interaction Specification (Phase 6)

> **North Star**: Motion at ELECTROCART is narrative, never decorative. It explains where the customer is (chapter changes), invites tactile inspection of craftsmanship (card tilt), and showcases precision engineering (hero scene). The utility layer (grid, filters, cart, checkout, account) receives zero scroll-linked animations and zero smooth-scroll hijack. Every effect respects user preference, degrades gracefully across three tiers, and remains 100% accessible with JavaScript disabled.

---

## 1. The Three Graceful Motion Tiers

ELECTROCART implements an automated capability probe on initial page load (`frontend/js/modules/capability.js`). The active tier is applied to `html[data-motion-tier]` and cached in `sessionStorage`.

| Parameter | Tier 1 (Full Motion) | Tier 2 (Lite Motion) | Tier 3 (Static / Reduced) |
| :--- | :--- | :--- | :--- |
| **Target Audience** | Modern desktop/laptop hardware, fine pointer, unconstrained network. | Tablets, mid-range Android, low-core CPUs, or weak GPUs. | `prefers-reduced-motion`, `saveData: true`, 2G/3G networks, low RAM (<4GB). |
| **Scroll Engine** | Lenis smooth scroll synced with GSAP ScrollTrigger ticker. | Native browser scrolling. | Native browser scrolling. |
| **Hero Plate** | Three.js WebGL scene with custom multiply blend shader & drift. | CSS float transform with subtle linear light-sweep gradient. | Perfectly static warm paper collectible plate. |
| **Chapter Wipe** | GSAP scrubbed polygon diagonal clip-path wipe. | IntersectionObserver-triggered CSS clip-path animation. | 150ms opacity crossfade or instant transition. |
| **Card Hover** | 3D perspective tilt (max 6deg) with dynamic specular sheen. | Subtle 2px vertical elevation lift (`translateY(-2px)`). | Static border/outline highlight without transform. |
| **Headline Cutouts** | 7.5s circular buffer cycle with 400ms float-crossfade. | 7.5s circular buffer cycle with 200ms opacity crossfade. | Static first cutout plate; zero looping animation. |
| **Small Motions** | Hairline rule draws once; headings reveal with 8px translate. | Instant rule display; headings reveal with opacity only. | Instant display, zero transforms or keyframe animations. |

---

## 2. Interaction & Motion Catalog

### A. Smooth Scroller & Inertia Normalization
- **Component**: `frontend/js/modules/scroller.js`
- **Trigger**: Continuous mouse wheel or trackpad scroll on desktop.
- **Duration**: Normalized inertia with 1.1s duration and exponential decay (`Math.min(1, 1.001 - Math.pow(2, -10 * t))`).
- **What it Communicates**: Pacing and weight appropriate for a physical biennial catalogue.
- **Strict Invariants**:
  - Starts **strictly** on Tier 1, fine pointer (`(pointer: fine)`), viewport width $\ge 1024\text{px}$, and `body[data-layer="editorial"]`.
  - **Never** starts on utility routes (`/cart/`, `/checkout/`, `/account/`, `/orders/`).
  - **Auto-pauses** whenever any `<dialog>` or modal drawer opens (mutation observer on `[open]`).
  - Keyboard navigation (PageUp, PageDown, Space, Arrows, Home, End) and accessibility Skip Links remain unhindered.
- **Tier Degradation**:
  - **Tier 1**: Active Lenis instance driving GSAP ticker.
  - **Tier 2 & 3**: Lenis is completely destroyed / uninitialized; 100% native scrolling.
  - **Reduced Motion**: Instantly killed; native scrolling preserved.

---

### B. Chapter Color Transitions & Diagonal Wipe
- **Component**: `frontend/js/modules/chapter_transitions.js` & `frontend/css/components/chapter-wipe.css`
- **Trigger**: Entering a new category chapter spread (`.spread[data-world]`).
- **Duration**:
  - Color Morphing: 450ms smooth transition via CSS `@property` on `--world-*` custom properties.
  - Diagonal Wipe: Scrubbed over 20% scroll distance (Tier 1) or 380ms keyframe (Tier 2).
- **What it Communicates**: Distinct chromatic chapters for each hardware category (e.g. Sennheiser amber vs. Keychron indigo), establishing spatial awareness.
- **Polygon Geometry**:
  - Diagonal entry: `polygon(0 0, 100% 0, 100% 0, 0 0)` to `polygon(0 0, 100% 0, 100% 100%, 0 100%)`.
- **Tier Degradation**:
  - **Tier 1**: GSAP ScrollTrigger scrubs the diagonal polygon clip-path based on exact scroll position.
  - **Tier 2**: IntersectionObserver triggers CSS keyframe animation `.chapter-wipe--active`.
  - **Tier 3**: Calm 150ms opacity crossfade; clip-paths disabled.
  - **Reduced Motion**: 150ms opacity fade or instant color token update.

---

### C. Technique H: Collectible Plate 3D Tilt
- **Component**: `frontend/js/modules/collectible_cards.js` & `frontend/css/components/editorial-plate.css`
- **Trigger**: Mouse cursor hover and move across `.plate-collectible` cards.
- **Duration**: Real-time pointer tracking throttled to `requestAnimationFrame`; 250ms spring return on `pointerleave`.
- **What it Communicates**: Tactile materiality, invites inspection of fine product finishes, mirrors holding an exhibition catalogue plate under gallery lighting.
- **Physics**:
  - Max pitch/yaw: $\pm 6^{\circ}$ clamped.
  - Perspective depth: `1000px`.
  - Dynamic specular glare: calculates cursor position $(X, Y)$ relative to card mat and positions a radial white gradient (`opacity: 0.12`).
- **Tier Degradation**:
  - **Tier 1**: Full 3D perspective tilt with specular highlight.
  - **Tier 2**: Flat 2D elevation lift (`translateY(-2px)`) with subtle drop shadow.
  - **Tier 3 & Touch**: Static card; focus ring on tab; no tilt or hover transform.

---

### D. Technique A: Cycling Inline Headline Cutouts
- **Component**: `frontend/js/modules/headline_cutouts.js`
- **Trigger**: Idle time on editorial homepage hero headline.
- **Duration**: 7.5s pause between cycles; 400ms crossfade with 3px float.
- **What it Communicates**: The breadth of curated objects in the collection without overwhelming typography.
- **State Guards**:
  - Cycles paused if tab is hidden (`document.hidden`).
  - Cycles paused if hero is scrolled offscreen (`!isIntersecting`).
  - Cycles paused if user is hovering or keyboard-focusing inside hero headline (`:hover`, `:focus-within`).
  - Zero DB queries: data derived in-memory from pre-fetched hero products and embedded via `json_script:"hero-cutouts-data"`.
- **Tier Degradation**:
  - **Tier 1**: 400ms float-crossfade.
  - **Tier 2**: 200ms opacity crossfade without vertical float.
  - **Tier 3 & Reduced Motion**: Looping stopped entirely. First cutout remains statically visible.

---

### E. Hero WebGL 3D Scene
- **Component**: `frontend/js/modules/hero_webgl.js`
- **Trigger**: Loading the homepage on Tier 1 hardware when the hero plate enters the viewport.
- **Duration**: Continuous gentle idle drift ($\sin(t \times 0.0012) \times 0.04$); 2.5s specular light sweep on entry.
- **What it Communicates**: Precision consumer tech presented like museum horology.
- **Shader Architecture**:
  - Custom multiply blend shader: `output = textureColor.rgb * uWorldBg`.
  - Eliminates harsh white studio backgrounds seamlessly into warm paper `--world-bg`.
  - Diagonal specular band: `smoothstep` sweep across UV coordinates.
- **Safety & Lifecycle Guards**:
  - **Code Splitting**: Dynamic `import("./modules/hero_webgl.js")` ensures Three.js (621 kB chunk) is **never requested** in Tier 2 or 3.
  - **Render Loop Control**: Pauses `requestAnimationFrame` when hero is offscreen or tab is backgrounded.
  - **Context Lost Recovery**: Traps `webglcontextlost` and disposes all geometries, materials, and textures, reverting cleanly to CSS presentation.
  - **Owner 3D Model Path**: Optional GLTFLoader checks `mountContainer.dataset.heroModel`. Absent by default; uses photo plane.
- **Tier Degradation**:
  - **Tier 1**: Three.js WebGL scene with multiply shader and pointer parallax.
  - **Tier 2**: Pure CSS float animation (`translateY(-4px)`) and CSS linear-gradient light sweep.
  - **Tier 3 & No-JS**: Static collectible plate with zero animation.

---

### F. Technique J: Dual-Thumb Price Histogram
- **Component**: `frontend/js/modules/price_histogram.js` & `frontend/css/components/price-histogram.css`
- **Trigger**: Dragging or keyboard-navigating range slider thumbs on category filter drawer.
- **Duration**: Instant visual feedback; 250ms debounced live count requests.
- **What it Communicates**: Price distribution transparency across catalog inventory with immediate count feedback.
- **Accessibility & Mechanics**:
  - ARIA slider pattern (`role="slider"`, `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, `aria-valuetext` in INR).
  - Keyboard step navigation: Arrow keys, PageUp/PageDown ($10\times$ step), Home/End.
  - Log-scaled SVG histogram bars highlighting real-time in-range vs out-of-range status.
  - Debounced fetch to rate-limited `/c/<slug>/count/` endpoint with `AbortController` cancellation.
  - 100% functional with JS disabled: submits native `min_price` and `max_price` form inputs.

---

### G. Small Micro-Interactions
- **Component**: `frontend/js/modules/small_motions.js` & `frontend/css/utilities.css`
- **Hairline Draw**: Section dividing rules draw from left to right (`scaleX(0)` to `scaleX(1)`) over 450ms once upon entering viewport (editorial only).
- **Heading Reveal**: Editorial section titles fade in with an 8px translate (`translateY(8px)` to `0`) over 420ms once upon entering.
- **Bag Count Feedback**: When an item is added, `announceBagUpdate` triggers a polite announcement in `#live-announcer` (`aria-live="polite"`) and a gentle 2px vertical badge nudge (`translateY(-2px)`).
- **Strict Invariant**: No bouncing carts, no looping attention traps, no popups.

---

## 3. User Controls & Overrides

1. **Persistent Reduced Motion Toggle**:
   - Location: Storefront footer (`#toggle-reduce-motion`).
   - Action: Toggles between manual `"reduced"` and `"auto"`. Persists to `localStorage.getItem("electrocart_motion_pref")`.
   - Accessible state: `aria-pressed="true|false"` with live label update.
2. **Developer Motion Override Query**:
   - Usage: `?motion=1`, `?motion=2`, or `?motion=3` forces the tier.
   - Protection: Active only when `settings.MOTION_DEBUG` is True (development / test). Stripped cleanly by `MotionDebugMiddleware` in production.
