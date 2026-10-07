# KNOWN ISSUES & BLOCKERS LOG (ELECTROCART)

### Active Operational Items (Handoff to Store Owner)
- **ISS-005 (Operational / Business Configuration)**: Legal policy pages (`/legal/terms/`, `/legal/privacy/`, `/legal/shipping/`, `/legal/refunds/`) and invoice seller blocks contain statutory templates requiring the store owner to input their registered legal entity name, GSTIN, physical address, and grievance officer contact before opening to live traffic. Documented in `docs/FINAL_REPORT.md`.
- **ISS-008 (Operational / Media Migration)**: Catalog sample data currently references 7,149 external Amazon CDN images. The platform provides full fallback silhouette plates and loading guards, but real product photography and WebGL GLTF 3D assets must be ingested before production marketing launches per `ASSETS.md`.

### Historical Resolved Issues
- **ISS-001 (Resolved - Phase 1)**: PostgreSQL 18 password authentication failure for role `electrocart`.
  - *Resolution*: Configured native SQLite WAL mode (`DATABASE_URL=sqlite:///db.sqlite3`) with zero concurrency bottlenecks per Standing Orders Section 5.
- **ISS-002 (Resolved - Phase 1)**: `No module named 'dj_database_url'` when running naked `python`.
  - *Resolution*: Root caused to host environment resolution pointing to global Python 3.13 instead of the virtualenv. Explicitly targeting `.venv\Scripts\python.exe` resolved all dependencies.
- **ISS-003 (Resolved - Phase 2)**: `django_vite.W001` missing manifest file warning.
  - *Resolution*: Seeded placeholder `static/dist/.vite/manifest.json` for development and testing pipelines prior to running Vite production builds.
- **ISS-004 (Resolved - Phase 4)**: Catalog sample data image resilience.
  - *Resolution*: Built SVG silhouette plates, lazy loading with `decoding="async"`, and client-side micro-fallback (`image-fallback.js`) ensuring broken or slow images never collapse card layouts.
- **ISS-006 (Resolved - Phase 7)**: Statutory GST PDF invoices required Indian Rupee (₹) symbol rendering across Windows and Linux without host system font dependencies.
  - *Resolution*: Registered pure Python ReportLab TTF font with TrueType unicode glyph mappings (`DejaVuSans.ttf`), ensuring pixel-perfect statutory PDF rendering and test compliance.
- **ISS-007 (Resolved - Phase 7)**: Mobile viewport (390px) horizontal overflow defects on price histogram slider, cart line items, and statutory invoice data tables.
  - *Resolution*: Scoped histogram slider track margins to prevent thumb overflow (`overflow-x: clip`), added `@media (max-width: 639px)` line-item wrapping in cart, and wrapped wide statutory 9-column tables in responsive touch-scroll wrappers (`.table-responsive { overflow-x: auto; }`). Zero horizontal overflow across all 26 audited viewports.
