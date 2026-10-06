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
