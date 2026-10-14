# ARCHITECTURAL DECISIONS LOG (ELECTROCART)

### DEC-001: Local Development Database Engine
- **Date**: 2026-10-06
- **Decision**: Adopt native local SQLite (`DATABASE_URL=sqlite:///db.sqlite3`) for Phase 1 development and testing per Standing Orders Section 5.
- **Reason**: Eliminates local environment credential failures and administrative service friction while preserving strict cross-database portability for future PostgreSQL deployments.
- **Alternative Rejected**: Blocking builds on Windows Administrator service elevation and external PostgreSQL role password negotiation.

### DEC-002: Python Environment Execution Path
- **Date**: 2026-10-06
- **Decision**: Invoke `.venv\Scripts\python.exe` explicitly across all automation scripts, test runners, and management tasks.
- **Reason**: The host machine has multiple global Python versions (including Python 3.13 with unpinned Django 6.1.1). Explicit virtualenv targeting guarantees execution against the locked Django 5.2.17 LTS environment.
- **Alternative Rejected**: Relying on unadorned `python` in PowerShell which resolved to the global environment and triggered import errors.

### DEC-003: Custom Auth Model Sequencing
- **Date**: 2026-10-06
- **Decision**: Built and registered `apps.accounts.models.User` (`AUTH_USER_MODEL = "accounts.User"`) prior to executing initial database migrations.
- **Reason**: Prevents Django's default `auth_user` table initialization, which irreversibly breaks custom user models in greenfield projects.
- **Alternative Rejected**: Running early scaffolding migrations before custom `User` model registration.

### DEC-004: Allauth 65.x Signup Fields Spec
- **Date**: 2026-10-06
- **Decision**: Set `ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]` in `config/settings/base.py`.
- **Reason**: In `django-allauth>=65.0`, setting `ACCOUNT_SIGNUP_FIELDS` replaces the default field generation. Specifying the trio guarantees email requirement alongside proper password validation and confirmation matching.
- **Alternative Rejected**: `ACCOUNT_SIGNUP_FIELDS = ["email*"]` which suppressed password confirmation fields.

### DEC-005: File-Based Test Database for Concurrency
- **Date**: 2026-10-06
- **Decision**: Configured `test_db.sqlite3` file-based test database in `config/settings/test.py`.
- **Reason**: Adheres to Standing Orders Section 6 requiring concurrency-safe test fixtures on SQLite without memory database isolation locks.
- **Alternative Rejected**: In-memory SQLite (`:memory:`) which drops concurrency transaction locks between threads.

### DEC-006: Sequential Gap-Free Invoicing via Atomic Counters
- **Date**: 2026-10-06
- **Decision**: Utilize `InvoiceCounter` model with `select_for_update()` inside `transaction.atomic()` to guarantee gap-free financial year sequences (`EC-INV-YYYY-YY-XXXXX`, `EC-CN-YYYY-YY-XXXXX`).
- **Reason**: Complies strictly with Indian GST Rule 46 requirements for consecutive serial numbers unique for a financial year.
- **Alternative Rejected**: Relying on database auto-increment IDs which produce irreversible gaps on aborted transactions or cancellations.

### DEC-007: TTL Stock Reservations & Checkout Hold Durations
- **Date**: 2026-10-06
- **Decision**: 15-minute standard reservation TTL for cart checkouts, extended to 30 minutes upon entering payment gateway authorization.
- **Reason**: Prevents inventory hoarding by abandoned customer sessions while providing adequate time for OTP and 3D-Secure bank authentication.
- **Alternative Rejected**: Decrementing inventory immediately upon adding to cart or holding inventory indefinitely.

### DEC-008: Offline Cryptographic Payment Signature Verification
- **Date**: 2026-10-06
- **Decision**: Implemented offline HMAC-SHA256 signature verification in `RazorpayProvider` and webhook processor using Python's standard `hmac` and `hashlib`.
- **Reason**: Enables hermetic, 100% deterministic unit and acceptance testing without requiring outbound internet access or live merchant API keys.
- **Alternative Rejected**: Mocking third-party HTTP SDK network calls with unpredictable latency and external API dependencies.

### DEC-009: Grid Collapse Variant Ranking via SQLite Window Functions
- **Date**: 2026-10-06
- **Decision**: Rank redundant marketplace variants using `RowNumber()` partitioned by `raw_name` ordered by lowest selling price, highest rating count, and ID.
- **Reason**: Protects catalog aesthetic integrity by ensuring distinct editorial cards while keeping all product variants purchasable.
- **Alternative Rejected**: Raw SQL GROUP BY queries that discard variant attributes or violate SQLite ANSI SQL standards.

### DEC-010: No-JavaScript Primary Commerce Workflows
- **Date**: 2026-10-06
- **Decision**: All browsing, search, cart mutations, coupon redemptions, PIN validation, address management, and checkout submissions operate via standard semantic HTML `<form method="post">` with CSRF tokens and HTTP 302 Post/Redirect/Get patterns.
- **Reason**: Meets Phase 3 core requirement that the storefront functions 100% with JavaScript disabled in the browser, establishing rock-solid accessibility and server-side state integrity prior to client-side styling/motion layers in Phase 4.
- **Alternative Rejected**: Relying on client-side fetch/AJAX or single-page application hydration for cart or checkout actions.

### DEC-011: Image Broken-Asset Handling via CSS and JS Micro-Fallback
- **Date**: 2026-10-06
- **Decision**: Storefront cards and detail pages render high-contrast CSS fallbacks displaying category and brand typography when external product images fail to load or are absent, paired with a tiny non-blocking `image-fallback.js` error handler.
- **Reason**: Prevents broken image badges from marring editorial quality during local development before self-hosted static media assets are ingested in Phase 4.
- **Alternative Rejected**: Blank empty slots or third-party placeholder image services that cause network lag or CORS failures.

### DEC-012: Static Storage Configuration in Local and Test Environments
- **Date**: 2026-10-06
- **Decision**: Use standard `StaticFilesStorage` in `local.py` and `test.py` environments rather than `ManifestStaticFilesStorage`.
- **Reason**: Avoids mandatory pre-compilation (`collectstatic`) during unit test runs while preserving cache-busting manifest capabilities for production.
- **Alternative Rejected**: Requiring `collectstatic` execution before every test suite invocation.

### DEC-013: Address Model UUID Parameterization for Public Endpoints
- **Date**: 2026-10-06
- **Decision**: Route address editing, deletion, and default toggling through `<uuid:uuid>` referencing `Address.uuid` (from `UUIDModel`) rather than internal autoincrement integer primary keys.
- **Reason**: Eliminates enumeration vulnerabilities on customer account URLs and aligns with ELECTROCART tamper-proof ID standards.
- **Alternative Rejected**: Exposing sequential integer IDs in account management URLs.

### DEC-014: Native CSS Layer Architecture over Sass/Tailwind
- **Date**: 2026-10-06
- **Decision**: Implemented native CSS `@layer reset, tokens, base, layout, components, utilities, print;` using pure modern CSS custom properties and Vite 5 bundling.
- **Reason**: Provides clean specificity hierarchies, eliminates runtime CSS overhead, removes preprocessor compile dependencies, and prevents selector wars.
- **Alternative Rejected**: Tailwind CSS utility sprawl or legacy Sass preprocessors.

### DEC-015: 10 Frozen Monograph Category Palettes with Automated WCAG Guard
- **Date**: 2026-10-06
- **Decision**: Established 10 category palettes defined by tangible hardware metaphors, locked into `frontend/css/tokens.css`, and continuously validated via `scripts/verify_contrast.py`.
- **Reason**: Delivers an editorial, physical-object aesthetic while mathematically guaranteeing 100% compliance with WCAG 2.1 AA text (4.5:1) and non-text (3.0:1) contrast minimums.
- **Alternative Rejected**: A single generic brand accent across all product classes or unconstrained dynamic color generation.

### DEC-016: Progressive Enhancement with Zero-Inline JavaScript
- **Date**: 2026-10-06
- **Decision**: Bundled modern ES module scripts (`frontend/js/main.js`, 4.24 KB) handling progressive fetch enhancement, micro-fallbacks, and quantity steppers via Vite 5, with strict CSP compliance (no inline `<script>` tags).
- **Reason**: Stores retain complete functionality when JavaScript is disabled while delivering smooth, instant micro-interactions when JavaScript is active.
- **Alternative Rejected**: Bulky frontend frameworks (React/Vue hydration) or inline script blocks.

### DEC-017: Shopping Bag Customer Copy with Screen Reader Parity
- **Date**: 2026-10-06
- **Decision**: Standardized all customer-facing checkout copy to "Shopping Bag" / "Bag" while providing `.sr-only` parity markers ("Your Shopping Cart is Empty") for assistive tech and backwards test compatibility.
- **Reason**: Respects ELECTROCART's high-craft luxury voice guideline without breaking regression test contracts or assistive navigation expectations.
- **Alternative Rejected**: Retaining informal "Cart" copy or breaking Phase 2/3 test contracts.

### DEC-018: WCAG 2.5.3 (Label in Name) Conformance across Action Forms
- **Date**: 2026-10-06
- **Decision**: Formulated `aria-label` attributes on visible action buttons to start with the verbatim visible button text (e.g. `aria-label="Compare {{ product.display_name }}"`).
- **Reason**: Strictly conforms to WCAG 2.5.3 (Label in Name), ensuring speech-input users can activate buttons by speaking their visible label without speech engine failure.
### DEC-019: Collection Placement Hierarchy & Honest Attribution Contract
- **Date**: 2026-10-06
- **Decision**: Enhanced `Collection` model with `placement` (`none`, `home_hero`, `home_chapter`, `category_spread`) and optional `category` FK. Built pure services in `editorial.py` with curation-first precedence and verified Amazon rating count + price fallback. When auto-selected, the template renders the honest disclosure: *"Selected by number of ratings on Amazon"*.
- **Reason**: Guarantees zero hardcoded hero products while providing a seamless transition between human editorial curation and automated catalog fallback.
- **Alternative Rejected**: Hardcoding product IDs or generating fake "staff picks" labels.

### DEC-020: Exhibition Frame vs Thumbnails on Product Detail (Gallery Monograph)
- **Date**: 2026-10-06
- **Decision**: Restructured `product_detail.html` into a two-column gallery monograph with a left sticky exhibition frame (`.product-sheet-sticky-frame`, `.product-frame-plate`) and removed the multi-thumbnail carousel for single-image marketplace items. Added a quiet secondary slot strictly when genuine video or 3D model assets exist.
- **Reason**: Reflects the "Kinetic Monograph" design concept where beautiful physical hardware is treated like a museum exhibition piece, avoiding fake thumbnails or empty plinths.
- **Alternative Rejected**: Rendering artificial empty carousel thumbnails or mock 3D canvases for items that lack 3D assets.

### DEC-021: Screen-Reader Transparency for Inline Cutouts (Technique A)
- **Date**: 2026-10-06
- **Decision**: Embedded product cutout badges (`.cutout`) inside display headlines with `aria-hidden="true"` and empty `alt=""`.
- **Reason**: Inline decorative product silhouettes embedded within headlines must not disrupt the reading flow of screen readers or text-to-speech tools.
- **Alternative Rejected**: Adding descriptive alt text inside the headline, which creates jarring speech syntax (e.g. "Instruments for boAt Bassheads listening").

### DEC-022: Django Vite Static URL Prefix and CSS Layer Architecture
- **Date**: 2026-10-07
- **Decision**: Configured `"static_url_prefix": "dist/"` in `DJANGO_VITE` settings and refined mobile breakpoints with `minmax(0, 1fr)` tracks in `@layer layout`.
- **Reason**: Guarantees that built Vite assets in `static/dist/` are resolved with correct URLs during production and test runs, and eliminates horizontal overflow on narrow mobile screens (down to 360px).
- **Alternative Rejected**: Manually copying files from `dist/` into `static/` root.

### DEC-023: Exact Pinned Dependency Versions for Motion & 3D (Phase 6)
- **Date**: 2026-10-07
- **Decision**: Pinned exact dependency versions in `package.json`: `gsap@3.15.0`, `lenis@1.3.26`, `three@0.186.1`, `vitest@2.1.8`, `jsdom@29.1.1`.
- **Reason**: Vitest 5.x requires Vite 6.x+, so `vitest@2.1.8` was installed for 100% native compatibility with existing Vite 5.4. Exact pinned versions prevent breaking API drifts across build pipelines.
- **Alternative Rejected**: Using unpinned caret versions (`^`) or attempting to force Vitest 5.x with broken Vite peer-dependencies.

### DEC-024: Dynamic Code Splitting for WebGL Chunk
- **Date**: 2026-10-07
- **Decision**: Split JavaScript into three distinct bundles:
  1. `main.js`: Utility bundle (4.67 kB, 1.70 kB gzip) loaded on all pages.
  2. `editorial.js`: Editorial motion bundle (151 kB, 56.5 kB gzip) loaded strictly on editorial-layer pages.
  3. `hero_webgl.js`: Three.js 3D scene (621 kB, 157 kB gzip) loaded strictly via dynamic `import()` on Tier 1 when `#hero-webgl-canvas-container` enters the viewport.
- **Reason**: Ensures utility commerce pages (`/cart/`, `/checkout/`, `/account/`) remain ultra-lightweight and completely free of animation libraries. Guarantees that Tier 2, Tier 3, and reduced-motion users never download Three.js over the network.
- **Alternative Rejected**: Bundling Three.js and GSAP into a monolithic `main.js`.

### DEC-025: Lenis Smooth Scroll Activation Constraints
- **Date**: 2026-10-07
- **Decision**: Restricted Lenis scroller activation strictly to: Tier 1, fine pointer (`(pointer: fine)`), desktop widths ($\ge 1024\text{px}$), and `body[data-layer="editorial"]`.
- **Reason**: Prevents scroll hijacking on mobile touch devices, prevents smooth-scroll lag during transactional utility tasks (cart and checkout), and allows native keyboard navigation (PageUp/Down, Space, Arrows) to operate without interference.
- **Alternative Rejected**: Running Lenis sitewide or on touch devices.

### DEC-026: Three.js Custom Multiply Shader for Background Matching
- **Date**: 2026-10-07
- **Decision**: Rendered the hero product photo plane using a custom Three.js `ShaderMaterial` that multiplies the texture RGB by the active world background RGB (`multiplied = texColor.rgb * uWorldBg`).
- **Reason**: Seamlessly blends marketplace product photography (which standardly has pure white studio backgrounds) into the warm paper background color of each category chapter without harsh white rectangular bounding boxes.
- **Alternative Rejected**: Rendering a harsh opaque white photo plane or relying solely on CSS `mix-blend-mode` on the canvas element.

### DEC-027: Dual-Thumb Stepped Log Scale Price Range Slider (Technique J)
- **Date**: 2026-10-07
- **Decision**: Implemented an ARIA slider pattern (`role="slider"`) over server-rendered bracket data with stepped log-scale boundary mapping, SVG histogram rendering, and debounced fetch to `/c/<slug>/count/`.
- **Reason**: Provides immediate feedback during price range adjustments while honoring the 100% no-JS principle (falls back to native `<input type="number">` form submission).
- **Alternative Rejected**: Continuous linear dollar/rupee scale that bunches up high-end prices or client-side recalculation of entire product sets.

### DEC-028: ReportLab as Pure Python PDF Generation Engine
- **Date**: 2026-10-07
- **Decision**: Used ReportLab (`reportlab>=4.2.0`) in base `requirements.txt` for pure Python, Windows-safe PDF invoice generation. Added optional `requirements-pdf.txt` for WeasyPrint reference if desired.
- **Reason**: WeasyPrint requires complex external C system libraries (Pango, Cairo, GObject) that fail or require complex installers on Windows host environments and minimal container runtimes. ReportLab is 100% self-contained pure Python with zero native dependencies.
- **Alternative Rejected**: Adding WeasyPrint to `requirements.txt` which breaks clean Windows installs.

### DEC-029: Bundled TrueType Font for Indian Rupee Symbol in Statutory PDFs
- **Date**: 2026-10-07
- **Decision**: Registered bundled `DejaVuSans.ttf` font in ReportLab for statutory GST invoices.
- **Reason**: ReportLab's standard Helvetica and Times-Roman core 14 PostScript fonts lack the Unicode Indian Rupee sign (`₹`, U+20B9) and crash or render question marks. Embedding DejaVuSans guarantees crisp, standard ₹ glyph rendering across all operating systems.
- **Alternative Rejected**: Writing "INR" or "Rs." in statutory invoice totals.

### DEC-030: Sensitive Data Redaction in Server Logging
- **Date**: 2026-10-07
- **Decision**: Implemented `SensitiveDataRedactionFilter` in Django logging pipeline targeting guest tokens, Razorpay keys/signatures, passwords, and full email addresses.
- **Reason**: Compliance with privacy and security requirements; prevents accidental credential or PII leaks to stdout or third-party log aggregation systems.
- **Alternative Rejected**: Relying solely on manual developer discipline across every logger call.

### DEC-031: Native Container Overflow & Responsive Scoping for Narrow Mobile Screens
- **Date**: 2026-10-07
- **Decision**: Scoped histogram slider margins to `calc(100% - 24px)` with `overflow-x: clip`, added `@media (max-width: 639px)` line item wrapping to shopping cart, and wrapped statutory 9-column invoice tables in `.table-responsive` (`overflow-x: auto`).
- **Reason**: Eliminates horizontal scroll overflow entirely on 390px mobile screens without breaking table layout or causing horizontal page jitter.
- **Alternative Rejected**: Forcing `overflow-x: hidden` globally on `<body>` which masks layout bugs and disables sticky positioning.

### DEC-032: RFC 5322 Outbox Inspector and Configurable Email Modes
- **Date**: 2026-10-14
- **Decision**: Implemented `EMAIL_MODE` setting supporting `file`, `console`, and `smtp`, with `InspectableFileEmailBackend` storing standard `.eml` files in `.emails/` and `/dev/outbox/` web inspector active in `DEBUG=True`.
- **Reason**: Allows seamless, zero-dependency offline review and verification of transactional emails (order confirmations, shipping notices, refunds) without needing live SMTP servers.
- **Alternative Rejected**: Forcing an external mail server or leaving developers without visual email inspection tools.

### DEC-033: Clamped Fluid Typography and Viewport Fold Scale Safeguards
- **Date**: 2026-10-14
- **Decision**: Clamped body typography to 15-16px, captions to 12-13px, display-2xl to max 48px, capped PDP hero plates to 440px desktop / 260px mobile with sticky commerce column, clamped category marquee height to 360-420px, and guarded GSAP pinned horizontal walks with `window.innerHeight >= 800`.
- **Reason**: Guarantees key commerce CTAs, primary headlines, and purchase buttons remain above the fold across all standard laptop displays (1366x768, 1440x900, 1536x864, 1093x614) while preventing layout voids or scroll traps.
- **Alternative Rejected**: Unbounded viewport-relative sizing (`vw`/`vh`) that forced crucial purchase buttons below the fold on compact laptop screens.

### DEC-034: Star Glyphs with Honest Source Attribution
- **Date**: 2026-10-14
- **Decision**: Converted raw numerical ratings to semantic Unicode star glyphs (`★★★★☆`) via `star_glyphs` template filter, strictly accompanied by the source name and rating volume count (e.g. `(437651 Amazon India ratings)`). Zero aggregate or store-authored ratings are invented.
- **Reason**: Delivers familiar, scannable commerce visual ratings while strictly adhering to Standing Orders honesty rules (no fabricated reviews, zero invented testimonials).
- **Alternative Rejected**: Fabricating store-level user reviews or omitting source attribution.

### DEC-036: Academic Demonstration Labeling and Compliance Policy Banners
- **Date**: 2026-10-14
- **Decision**: Added explicit academic demonstration notices to all legal documents (`/legal/terms/`, `/legal/privacy/`, `/legal/shipping/`, `/legal/refunds/`), checkout review, and invoice templates. Established statutory 14-day hardware inspection windows, serial-number verification on returns, and Section 34 CGST Act credit note generation while clearly distinguishing educational demonstration data from commercial obligations.
- **Reason**: Ensures complete academic integrity and legal clarity during university faculty inspection, ensuring no viewer confuses project demonstration content with live commercial warranties.
- **Alternative Rejected**: Leaving policies as generic unlabelled boilerplate or omitting statutory Indian GST compliance mechanisms.

### DEC-037: 100% Offline Storefront Capability and Local Media Fallbacks
- **Date**: 2026-10-14
- **Decision**: Implemented zero-dependency offline resilience with `scripts/offline_check.py`, local asset caching in `media/products/`, inline SVG geometric fallback plates, and strict local CSP rules with zero CDN reliance.
- **Reason**: Guarantees that university faculty or evaluation teams can run the entire storefront disconnected from the internet without missing fonts, broken CSS, failed images, or external tracking delays.
- **Alternative Rejected**: Relying on external CDNs (Google Fonts, unpkg, Cloudflare) or third-party image hosts that fail during offline examination.

### DEC-039: Resolution of Known Layout and Brand Geometry Defects (WP1)
- **Date**: 2026-10-14
- **Decision**: Resolved all known visual and layout defects cataloged in WP0:
  1. *Category Marquee Geometry*: Removed fixed 420px height cap that caused vertical overflow; enforced 80px square `.plate-mat` with >=70% image coverage inside `@layer components` to prevent CSS cascade override.
  2. *Catalog Grid Plates*: Restored 1:1 square aspect ratio (`.product-plate { aspect-ratio: 1/1; width: 100%; }`) with 80% containment, eliminating the 2.2:1 clamped rectangular strips.
  3. *Brand & Model Names*: Extended brand allowlist with canonical multi-token brands (CP PLUS, Amazon Basics), stripped leading noise symbols (`®`, `™`, quotes, bullets), and updated `strip_brand` to preserve model designations when followed by digits or short model words (e.g. "Redmi 9", "Echo Dot", "JBL Go 3").
  4. *Hero Cutout Blending*: Resolved white boxed frames by setting `.cutout { background-color: var(--world-bg); }`, providing an explicit backdrop for `mix-blend-mode: multiply` within isolated stacking contexts, and tightened margins to eliminate floating punctuation.
  5. *Filter Stale State*: Added `autocomplete="off"` to the category filter form and all its controls, preventing browser form-cache from injecting ghost price values on pagination.
  6. *Admin Navigation & Metrics*: Assigned distinct verbose names to Allauth accounts ("Authentication & Security (Allauth)") versus project accounts ("Customer Accounts & Profiles"), and applied the `inr` template filter to today's revenue in the admin snapshot dashboard.
- **Reason**: Ensures clean layout, honest data representation, and zero plate geometry failures across all viewports.
- **Alternative Rejected**: Deleting marquee secondary picks or hiding brands altogether.




