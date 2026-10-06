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
