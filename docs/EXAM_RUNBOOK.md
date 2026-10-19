# University Examination Runbook
**ELECTROCART Monograph Storefront**  
*6-Minute Live Demonstration Script, Faculty Q&A Defense, and Fallback Protocol*

---

## 1. Demonstration Setup & Pre-Flight

Before inviting the evaluation committee:

1. **Activate Virtual Environment**:
   ```powershell
   .venv\Scripts\activate
   ```
2. **Confirm Clean Database & Seed Data**:
   ```powershell
   python scripts/db_summary.py
   ```
   *Verify 40 tables present, PRAGMA integrity check = ok, PRAGMA foreign_key_check = 0 violations.*
3. **Start Test Server**:
   ```powershell
   python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
   ```
4. **Open Browser Windows**:
   - Window 1 (Main Presentation): `http://127.0.0.1:8000/` (Storefront Home)
   - Window 2 (Dev Outbox Inspector): `http://127.0.0.1:8000/dev/outbox/`
   - Window 3 (Django Admin): `http://127.0.0.1:8000/admin/` (pre-authenticated with demo admin credentials from `docs/DEMO_CREDENTIALS.local.md`)
   - Terminal (Side by side): Prepared for verification commands.

---

## 2. Six-Minute Demonstration Script

| Timestamp | Phase | Action & What to Show | Spoken Narrative Key Points |
| :--- | :--- | :--- | :--- |
| **0:00 - 1:00** | **The Monograph Storefront** | Open `http://127.0.0.1:8000/`. Scroll from hero through Chapter 01 (Audio) to Chapter 02 (Smartphones). | *"ELECTROCART treats e-commerce as a printed monograph rather than a screaming bazaar. Notice the typography: Newsreader display paired with Inter body. As we scroll, the fixed chapter counter tracks position without scroll lag. Product cutouts dissolve seamlessly into tonal plates using mathematical multiply blending, eliminating artificial white box borders."* |
| **1:00 - 2:00** | **Catalog & Density Hierarchy** | Click **Categories** in header, then select **Smartphones** (`/c/smartphones/`). Toggle Brand and Price filters. | *"Here is the category catalog. Standard e-commerce templates suffer from severe vertical voiding or oversized hero cards. We have strictly clamped card heights to 200–260px and marquee grids to 360–420px, ensuring listings stay visible above the fold on all standard laptop displays. Notice the star ratings: these are honest, pulling real Amazon India rating distributions with clear source attribution—zero fabricated reviews."* |
| **2:00 - 3:00** | **Product Detail & Commerce Polish** | Click on a product (e.g. HDMI Cable). Enter PIN `560001` in the delivery estimator. Scroll to Recently Viewed. | *"On the Product Detail Page, notice the dual-column layout: the purchase card remains sticky while media scrolls cleanly. The inline PIN delivery estimator queries our logistics engine, returning exact transit days and carrier tier. Notice the Available Coupons box showing active discount codes. At the bottom, our Recently Viewed shelf runs entirely in client-side localStorage—zero tracking cookies, zero surveillance."* |
| **3:00 - 4:00** | **Cart, Two-Way Preservation & Checkout** | Click **Add to Bag**. On `/cart/`, click **Save for Later**, then click **Move to Bag**. Click **Proceed to Checkout**. | *"In the shopping cart, we engineered two-way item preservation: shoppers can save items for later without losing quantity state or clearing their bag. Notice the transparent tax breakdown: CGST and SGST calculated down to the rupee. Let's proceed to checkout as a guest. The checkout gateway provides a clean, frictionless path without forcing account creation."* |
| **4:00 - 5:00** | **Order Lifecycle, Email & GST Invoice** | Complete guest checkout with Cash on Delivery. On success page, click **Download Tax Invoice (PDF)**. Switch to Outbox tab. | *"We place the order. On the confirmation screen, a sequential order identifier is generated. Clicking 'Download Tax Invoice' yields a PDF adhering to Section 31 of the CGST Act, complete with HSN breakdown and Indian numbering words. In our developer outbox tab, we can inspect the RFC 5322 MIME email dispatched instantly with order details."* |
| **5:00 - 6:00** | **Operations Dashboard & System Rigor** | Switch to Admin window (`/admin/`). Show Operations Snapshot. Run `db_summary.py` in terminal. | *"Behind the storefront is a hardened operations console. Our custom dashboard aggregates orders today, total revenue using Python Decimal precision (never floating-point), and low-stock alerts. Finally, in the terminal, our database audit verifies 40 normalized tables with zero foreign key violations. The entire system has 288 passing automated tests and runs 100% offline."* |

---

## 3. Faculty Q&A Preparation & Defense

### Q1: Why did you choose SQLite for development instead of PostgreSQL?
> **Answer**:  
> SQLite provides zero-configuration portability, enabling any evaluator to clone and inspect the project without provisioning external database daemons. However, the application is strictly architected for Twelve-Factor deployment: the Django ORM and settings use `dj-database-url`, allowing seamless switching to PostgreSQL 16+ via a single `DATABASE_URL` environment variable. All database queries use ACID transactions and standard SQL.

### Q2: How does the system handle high-concurrency race conditions during flash sales or stock depletion?
> **Answer**:  
> We implemented atomic conditional `UPDATE` statements combined with time-bound inventory reservations inside `apps/inventory/services/reservation_service.py`. When a customer initiates checkout within a database transaction, available physical stock is queried against active, unexpired reservations. If available stock satisfies the cart quantity, a reservation record is created atomically. If two users attempt to purchase the last unit simultaneously, the conditional update and reservation check ensure the second transaction safely rejects with an `OutOfStockError` rather than overselling. On PostgreSQL deployments, this is additionally backed by `select_for_update()`.

### Q3: How is Goods and Services Tax (GST) calculated across state lines?
> **Answer**:  
> Per statutory Indian tax law, GST calculation depends on the **Place of Supply**:
> - If the shipping address is within Gujarat (home state code `24`), the system computes **Intra-State GST**: splitting the tax equally into **CGST (9%)** and **SGST (9%)**.
> - If the shipping address is outside Gujarat (e.g., Maharashtra `27` or Delhi `07`), the system computes **Inter-State GST**: charging **IGST (18%)**.  
> All calculations use Python `Decimal` with `ROUND_HALF_UP` to prevent financial penny rounding errors.

### Q4: Why are there no countdown timers, flash banners, or aggressive popups?
> **Answer**:  
> This was a deliberate architectural decision documented in our Standing Orders. High-end consumer hardware platforms (like Braun, Teenage Engineering, and Apple) communicate confidence through restraint and typography. Urgency countdowns and fake "Only 1 left!" badges are manipulative dark patterns. Every badge on ELECTROCART corresponds to verified database inventory, and ratings cite real Amazon India review distributions.

### Q5: How did you ensure accessibility (a11y) and performance on mobile devices?
> **Answer**:  
> The site complies with **WCAG 2.1 AA** standards:
> - High-contrast text exceeding the 4.5:1 ratio.
> - Minimum 44×44px interactive tap targets across all viewports.
> - Full keyboard navigability with visible `:focus-visible` outline rings.
> - `@media (prefers-reduced-motion: reduce)` disables GSAP animations and smooth scroll.
> - Fluid typography clamped with CSS `clamp()`, ensuring primary content stays above the fold on laptops and mobile devices alike.

---

## 4. Emergency Fallback Protocol

If something unexpected occurs during the live examination:

### Issue A: Port 8000 is occupied
```powershell
# Identify and terminate stale process, or start on alternate port
python manage.py runserver 127.0.0.1:8080 --settings=config.settings.local
```

### Issue B: Database is in an unexpected state or modified by prior tests
```powershell
# Run the idempotent setup_demo command to instantly reset and reseed
python manage.py setup_demo
```

### Issue C: Browser displays stale CSS or cached bundle
- Press `Ctrl + Shift + R` (or `Ctrl + F5`) in Chrome/Firefox to force a full cache refresh.

### Issue D: Need to prove test coverage and stability instantly
```powershell
# Run full automated test suite (288 tests in ~8 seconds)
pytest
```
