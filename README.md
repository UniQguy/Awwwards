# ELECTROCART — Concept 2: The Kinetic Monograph

ELECTROCART is an award-caliber consumer electronics and accessories storefront for India (currency INR ₹), delivered as a server-rendered Django 5.2 LTS application. It combines mathematical commerce correctness with an editorial design system inspired by physical exhibition monographs.

---

## Current Status: Phase 4 Complete
- **Phase 1 (Foundation & Catalog)**: SQLite database, custom accounts, catalog audit, 100% tax and shipping engine with dual GST calculation (CGST/SGST vs IGST).
- **Phase 2 (Commerce Engine)**: Concurrency-tested stock reservation, cart, wishlist, coupons, orders, gap-free financial invoices, offline Razorpay & COD verification, admin.
- **Phase 3 (Storefront)**: Semantic, accessible HTML storefront working 100% with JavaScript disabled.
- **Phase 4 (Design System & Utility Layer)**:
  - 10 frozen monograph category worlds in `frontend/css/tokens.css` with 100% WCAG 2.1 AA compliance (0 violations).
  - Fluid typography clamp scale (`--step--2` to `--step-7`) and 4px spatial grid.
  - Native CSS layer architecture: `@layer reset, tokens, base, layout, components, utilities, print`.
  - Vite 5 asset bundling (`static/dist/css/styles-*.css` at 54.15 kB, `static/dist/js/main-*.js` at 4.24 kB).
  - High-visibility keyboard focus rings, zero horizontal overflow across 4 viewports (390px, 768px, 1280px, 1920px).
  - Zero critical/serious axe-core accessibility violations.

---

## Architecture & Technology Stack
- **Framework**: Django 5.2.17 LTS (Python 3.12 / 3.13 virtual environment)
- **Database**: SQLite (local development & concurrent file-based test suite)
- **Frontend Pipeline**: Vite 5 + `django-vite` asset loader
- **CSS Architecture**: Pure CSS custom properties & native `@layer` cascade
- **Currency & Regionalization**: Indian Rupee (`₹`), dual-rate GST (Rule 46 compliant), PIN code carrier estimation
- **Quality Gates**: Playwright Chromium test harness, axe-core 4.x accessibility auditing, automated contrast verification matrix

---

## Quick Start

### 1. Environment Activation
```powershell
# Activate local virtual environment
.\.venv\Scripts\Activate.ps1
```

### 2. Database & Migrations
```powershell
.venv\Scripts\python.exe manage.py migrate
```

### 3. Build Frontend Assets
```powershell
npm run build
```

### 4. Run Development Server
```powershell
.venv\Scripts\python.exe manage.py runserver
```
Visit the store at `http://127.0.0.1:8000/`.

---

## Verification & Quality Gates

### Run Test Suite (145 tests)
```powershell
.venv\Scripts\python.exe manage.py test
```

### Automated Contrast Verification (70 category pairings + status + focus)
```powershell
.venv\Scripts\python.exe scripts/verify_contrast.py
```

### CSS Layer Discipline & Token Compliance Audit
```powershell
.venv\Scripts\python.exe scripts/css_audit.py
```

### Storefront Internal Link Crawler (80 URLs)
```powershell
.venv\Scripts\python.exe scripts/crawl_site.py
```

### Axe-Core Accessibility Audit
```powershell
.venv\Scripts\python.exe scripts/a11y_check.py
```

### Responsive Visual QA Screenshot Harness
```powershell
.venv\Scripts\python.exe scripts/screenshots.py
```
Outputs are saved to `reports/screenshots/`.

---

## Project Documentation
- [Standing Orders](docs/STANDING_ORDERS.md)
- [Design System Guide](docs/DESIGN_SYSTEM.md)
- [Architectural Decisions Log](docs/DECISIONS.md)
- [Ledger of Models & Contracts](docs/LEDGER.md)
- [URL Routing Map](docs/URLS.md)
- [Voice & Microcopy Rules](docs/COPY.md)
- [Phase 1 Report](docs/phase-1-report.md)
- [Phase 2 Report](docs/phase-2-report.md)
- [Phase 3 Report](docs/phase-3-report.md)
- [Phase 4 Report](docs/phase-4-report.md)
