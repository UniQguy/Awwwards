# Accessibility Audit & Compliance Report (WCAG 2.1 AA)

**Standard Applied:** WCAG 2.1 Level AA  
**Audit Date:** October 7, 2026  
**Auditor:** Automated axe-core 4.10.2 + Playwright Headless Engine + Manual Keyboard Protocol  
**Compliance Status:** Fully Compliant (Zero Critical, Serious, or Moderate Violations)

---

## 1. Automated axe-core Audit Results

Automated accessibility audits were executed using `axe-core` across both Desktop (1280×800) and Mobile (390×844) viewports.

| Page / Flow | URL | Viewport | axe-core Rules Evaluated | Violations | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Homepage** | `/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Category Index** | `/categories/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Category Monograph** | `/c/earphones-headphones/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Product Sheet** | `/p/boat-bassheads-100.../` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Shopping Bag** | `/cart/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Checkout Start** | `/checkout/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Brand Directory** | `/brands/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Sign In** | `/accounts/login/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |
| **Terms of Service** | `/legal/terms/` | 1280×800 & 390×844 | WCAG 2.0/2.1 A/AA | 0 | **PASS** |

---

## 2. Touch Target Size Compliance (WCAG 2.5.5 / 2.5.8)

Automated inspection via `scripts/audit_touch_targets.py` on a 390px mobile viewport:
- **Requirement:** Standalone interactive elements (buttons, inputs, dropdowns, icon triggers) must meet `>= 44×44 CSS px`.
- **Implementation:**
  - Standalone buttons (`.btn`, `.btn-icon`): Default `min-height: 44px`.
  - Compact buttons (`.btn-sm`): Enhanced with `@media (max-width: 860px), (pointer: coarse) { min-height: 44px; padding-block: var(--space-2); }`.
  - Alert dismissal triggers (`.alert-dismiss-btn`): Explicit `min-width: 44px; min-height: 44px; display: inline-flex; align-items: center; justify-content: center;`.
  - Checkbox controls (`.form-checkbox-group`, `.form-checkbox-label`): Wrapping labels provide touch target area `>= 44px` height with vertical centering.
  - Motion toggle trigger (`.motion-toggle-btn`): Fixed `min-height: 44px`.
- **Audit Outcome:** 0 undersized interactive targets across mobile pages (**PASS**).

---

## 3. High Contrast & Forced Colors Mode (`@media (forced-colors: active)`)

Tested for compatibility with Windows High Contrast Mode and system forced colors:
- **System Color Integration:** Explicit mappings to `Canvas`, `CanvasText`, `ButtonBorder`, `FieldText`, and `Highlight`.
- **Focus Rings:** Enforced `:focus-visible { outline: 2px solid Highlight; outline-offset: 2px; }`.
- **Borders & Plates:** Cards (`.product-card`, `.checkout-card`, `.editorial-plate`), tables, and dividers enforce `1px solid CanvasText` to preserve structural boundaries when background colors are stripped.
- **Controls:** Form inputs and native buttons render system-provided border cues (`ButtonBorder`, `FieldText`).

---

## 4. Zoom Reflow (WCAG 1.4.10 Reflow)

- **200% Zoom:** Content reflows seamlessly without clipping, overlapping, or horizontal scrolling.
- **400% Zoom (equivalent to 320px viewport):**
  - Fluid typography (`clamp()` steps) scales down proportionally.
  - Multi-column grids (`.grid-2`, `.grid-3`, `.catalog-layout`) collapse cleanly into a single vertical stack.
  - Horizontal scrolling is completely avoided (`scrollWidth <= clientWidth`).
  - All critical shopping actions (Add to Bag, Checkout, Order Tracking) remain fully accessible and operative.

---

## 5. Manual Accessibility & Keyboard Protocol Checks

1. **Screen Reader Announcement of Cart Count:**
   - Real-time updates utilize the global ARIA live region (`#live-announcer` with `aria-live="polite"` and `aria-atomic="true"`).
   - Adding or adjusting item quantity triggers an explicit verbal announcement: *"1 item added to shopping bag. Total items: 2"*.

2. **Live Region on Coupon Application:**
   - Feedback alerts inside the coupon container render with `role="status"` for applied discounts and `role="alert"` for invalid codes.

3. **Form Error Focus Management:**
   - Checkout validation errors automatically set keyboard focus to the first invalid input element (`focus()`), linked via `aria-describedby` to the specific error message text.
   - Form controls receive `aria-invalid="true"`.

4. **Keyboard Purchase Flow End-to-End:**
   - Skip link (`.skip-link`) allows direct jump to `#main-content` on Tab entry.
   - Entire catalog browse, product selection, cart modification, guest address entry, and order submission operable exclusively via `Tab`, `Shift+Tab`, `Enter`, and `Space`.
   - Focus outline is always prominent (`outline: 2px solid var(--world-accent); outline-offset: 2px;`).

---

## 6. Known Exceptions & Justifications

- None. All pages and core user journeys meet WCAG 2.1 Level AA without exceptions.

---

## 7. Accessibility Contact

For questions, audit requests, or reporting an accessibility obstacle:
- **Email:** accessibility@electrocart.local / support@electrocart.in  
- **Postal:** ELECTROCART RETAIL PRIVATE LIMITED, Attention: Accessibility Compliance Officer, Plot 104, Industrial Area Phase 2, Okhla, New Delhi – 110020.
