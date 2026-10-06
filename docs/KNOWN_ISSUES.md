# KNOWN ISSUES & BLOCKERS LOG (ELECTROCART)

### Active Issues
*None. All Phase 1 components, database migrations, and test suites are passing with zero errors.*

### Historical Resolved Issues
- **ISS-001 (Resolved)**: PostgreSQL 18 password authentication failure for role `electrocart`.
  - *Resolution*: Replaced with SQLite (`DATABASE_URL=sqlite:///db.sqlite3`) per Standing Orders Section 5.
- **ISS-002 (Resolved)**: `No module named 'dj_database_url'` when running naked `python`.
  - *Resolution*: Root caused to host environment resolution pointing to global Python 3.13 instead of the virtualenv. Explicitly targeting `.venv\Scripts\python.exe` resolved all dependencies.
- **ISS-003 (Resolved)**: `django_vite.W001` missing manifest file warning.
  - *Resolution*: Seeded placeholder `static/dist/.vite/manifest.json` for development and testing pipelines prior to running Vite production builds.
