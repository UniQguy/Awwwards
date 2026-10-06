# KNOWN ISSUES & BLOCKERS LOG (ELECTROCART)

### Active Issues / Non-Blocking Tracking
- **ISS-004 (Non-Blocking / By Design)**: Catalog sample data contains external CDN image URLs. A resilient CSS plate and client-side micro-fallback (`image-fallback.js`) handles absent/slow images gracefully. Phase 4 will ingest local optimized assets.
- **ISS-005 (Non-Blocking / Business Content)**: Standard shipping fee confirmation and legal templates (`/legal/terms/`, `/legal/privacy/`, etc.) carry explicit `[PLACEHOLDER]` disclaimers pending owner business registration data.


### Historical Resolved Issues
- **ISS-001 (Resolved)**: PostgreSQL 18 password authentication failure for role `electrocart`.
  - *Resolution*: Replaced with SQLite (`DATABASE_URL=sqlite:///db.sqlite3`) per Standing Orders Section 5.
- **ISS-002 (Resolved)**: `No module named 'dj_database_url'` when running naked `python`.
  - *Resolution*: Root caused to host environment resolution pointing to global Python 3.13 instead of the virtualenv. Explicitly targeting `.venv\Scripts\python.exe` resolved all dependencies.
- **ISS-003 (Resolved)**: `django_vite.W001` missing manifest file warning.
  - *Resolution*: Seeded placeholder `static/dist/.vite/manifest.json` for development and testing pipelines prior to running Vite production builds.
