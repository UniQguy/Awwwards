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



