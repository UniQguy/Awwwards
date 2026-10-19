# ELECTROCART — Concept 2: The Kinetic Monograph

**ELECTROCART** is a consumer electronics and accessories storefront for India (currency INR ₹), crafted as a server-rendered Django application.

Unlike noisy electronics marketplaces full of neon countdown timers and fake scarcity badges, Electrocart is built like an exhibition monograph: warm paper backgrounds, deep charcoal ink, a distinct accent color for each product category, honest pricing, and complete functionality without client-side JavaScript.

---

## 10-Step Setup Guide (Windows PowerShell)

Follow these 10 steps to run the complete store on a clean machine:

### Step 1: Open PowerShell and Clone the Repository
```powershell
git clone <repository-url> electrocart
cd electrocart
```

### Step 2: Create a Python Virtual Environment
Requires Python 3.12 or 3.13:
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements-dev.txt
```

### Step 5: Copy the Environment Configuration Template
```powershell
Copy-Item .env.example .env
```

### Step 6: Configure Required Values in `.env`
Open `.env` in Notepad and set three values:
1. `SECRET_KEY`: Set to any long random string (e.g. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`).
2. `SELLER_STATE`: Set your dispatch origin state, such as `Gujarat` or `Maharashtra` (required for Indian GST split).
3. `DATABASE_URL`: Defaults to `sqlite:///db.sqlite3` for effortless local setup.

### Step 7: Run Database Migrations
```powershell
python manage.py migrate
```

### Step 8: Ensure the Catalog CSV Exists and Import Catalog
Place `electronics_product.csv` at `data/electronics_product.csv` and run:
```powershell
python manage.py import_products --csv data/electronics_product.csv
```

### Step 9: Seed Demo Store Data
Creates categories, sample coupons, and courier delivery zones:
```powershell
python manage.py seed_demo
```

### Step 10: Start the Development Server
```powershell
python manage.py runserver
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser to browse the storefront.

---

## How to Build the Front-End Assets

If Node.js is installed on your system:
```powershell
npm install
npm run build
```
This compiles the CSS tokens and JavaScript bundles into `static/dist/`.

---

## How to Access the Admin and Create a Superuser

1. Create your administrator account:
   ```powershell
   python manage.py createsuperuser
   ```
2. Enter your email and password.
3. Open **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)** (or your custom `ADMIN_URL` if configured in `.env`).

---

## How to Curate the Homepage in the Admin

1. Log into the Django Admin.
2. Navigate to **Catalog > Collections**.
3. Create or edit a Collection:
   - Set **Placement** to:
     - `Home Hero`: Drives the 3 headline products in the top hero plate.
     - `Home Chapter`: Drives the category monographs displayed on the homepage.
     - `Category Spread`: Drives the top featured plate on category index pages.
   - Attach products via the **Featured Products** inline.
   - If no collections are curated, the storefront automatically chooses popular products and displays an honest sample badge.

---

## How to Replace Product Images

1. In the Django Admin, navigate to **Catalog > Products** and select an item.
2. Scroll to the **Product media items** inline.
3. You can either:
   - Upload a local image file (`.jpg`, `.png`, `.webp`, `.avif`, max 5MB).
   - Enter an external CDN photo URL.

---

## How to Configure Statutory Indian GST Details

To print statutory GST Tax Invoices instead of a Bill of Supply:
1. Open `.env`.
2. Populate the following seller variables:
   ```env
   SELLER_STATE=Gujarat
   SELLER_GSTIN=24ABCDE1234F1Z5
   SELLER_LEGAL_NAME=Electrocart Retail Private Limited
   SELLER_ADDRESS=100 Ashram Road, Ahmedabad, Gujarat 380009
   ```
3. Restart `runserver`. Invoices will immediately render with statutory CGST, SGST, IGST, HSN tables, and sequential gap-free numbering.

---

## How to Test Razorpay Online Payments

1. Sign up for a free test account at [Razorpay](https://razorpay.com).
2. Generate Test API Keys in Razorpay Dashboard > Settings > API Keys.
3. Add them to `.env`:
   ```env
   RAZORPAY_KEY_ID=rzp_test_YourKeyId
   RAZORPAY_KEY_SECRET=YourSecretKey
   RAZORPAY_WEBHOOK_SECRET=YourWebhookSecret
   ```
4. Restart the server. During checkout, selecting "Razorpay Online" will open the Razorpay payment modal with test card support.

---

## Running Automated Verification & Quality Gates

Run all automated test suites and audits with a single command:

```powershell
# Run the complete Launch Audit
python scripts/launch_audit.py

# Run the full Python test suite (289 tests)
python manage.py test

# Run front-end unit tests (52 tests across 7 test files)
npm test

# Run 100% offline verification audit
python scripts/offline_check.py

# Run zero-defect layout audit across 8 viewports
python scripts/layout_audit.py

# Run void and reveal defect audit
python scripts/void_audit.py

# Run full QA matrix and keyboard walkthrough
python scripts/full_qa.py
```

---

## Documentation Index

Comprehensive documentation is organized in `docs/`:
- [`docs/README.md`](docs/README.md): Master documentation table of contents.
- [`docs/EXAM_RUNBOOK.md`](docs/EXAM_RUNBOOK.md): 6-minute live demonstration script and faculty Q&A defense.
- [`docs/FEATURE_MATRIX.md`](docs/FEATURE_MATRIX.md): Traceability matrix mapping requirements to source files and tests.
- [`docs/DEPLOY_READINESS.md`](docs/DEPLOY_READINESS.md): Production hardening, Nginx, Systemd, and deployment runbook.
- [`docs/DATABASE_GUIDE.md`](docs/DATABASE_GUIDE.md): Non-developer database guide, ERD diagram, and inspection tools.
- [`docs/EMAIL_SETUP.md`](docs/EMAIL_SETUP.md): Transactional email modes and developer outbox inspector.
- [`docs/FLOW_REVIEW.md`](docs/FLOW_REVIEW.md): Commerce loophole review, concurrency locking, and security defenses.
- [`docs/MARKET_AUDIT.md`](docs/MARKET_AUDIT.md): Competitive commerce UX benchmark against top Indian platforms.
- [`docs/PLACEHOLDERS_TO_REPLACE.md`](docs/PLACEHOLDERS_TO_REPLACE.md): Production cutover checklist and credentials audit.
- [`docs/STANDING_ORDERS.md`](docs/STANDING_ORDERS.md): Architectural rules and honesty principles.
- [`docs/LEDGER.md`](docs/LEDGER.md): Canonical registry of models, fields, and services.
- [`docs/URLS.md`](docs/URLS.md): Full route map with views, permissions, and context.
- [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md): Kinetic Monograph typography, layout, and palettes.
- [`docs/ACCESSIBILITY.md`](docs/ACCESSIBILITY.md): WCAG 2.1 AA audit reports and keyboard navigation specs.
- [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md): Query optimization, caching headers, and database pragmas.
- [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md): Threat models, rate limits, and audit findings.
- [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md): Production deployment reference and environment variables.
