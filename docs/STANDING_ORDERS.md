STANDING ORDERS FOR THE ELECTROCART BUILD. Read fully. They apply to every phase. Save this message verbatim to docs/STANDING_ORDERS.md as your first action.

1. WHAT YOU ARE BUILDING
ELECTROCART: a premium, award-caliber electronics and accessories store for India (currency INR), delivered as a fully working, server-rendered Django 5.2 LTS application. Commerce correctness is non-negotiable; within that, design ambition is the goal. I am not a command-line expert; you do the work end to end.

2. AUTONOMY
- Never ask me to choose among options. Never present numbered option menus. Decide as a senior engineer and record each decision in docs/DECISIONS.md (decision, reason, alternative rejected).
- Do not ask permission to run commands, create/edit/delete files inside this repository, install packages from requirements files, run tests, or make local git commits. Do them.
- Stop only for a true blocker you cannot solve yourself. Log it in docs/KNOWN_ISSUES.md and continue with all remaining work.
- Keep going until the phase's Definition of Done is met. If a command fails, read the error, fix the cause, re-run. After 3 failed attempts on one problem, log it and move on; retry once at the end.
- If you run out of room: commit, write docs/phase-N-report.md (done / remaining), and end. I will reply "Continue Phase N from the report".

3. TRUTHFULNESS (non-negotiable)
- Report only results of commands you actually ran in this session. Paste real output (last ~20 lines). Mark anything not run as "NOT RUN" with the reason. Never write "Expected output", "Verbatim", or "Passing result" for something you did not run. Never claim a check passed from memory or inference.
- Never invent products, prices, specs, ratings, reviews, brands, awards, metrics, certifications, policies, delivery promises, or assets. Use dataset values, parsed values, or clearly labelled SAMPLE data.
- If unsure whether an API exists in the installed version, read the installed package source under .venv\Lib\site-packages (or its docs) and say what you verified. Otherwise mark it UNVERIFIED in a code comment and in docs/KNOWN_ISSUES.md.
- Never claim to have inspected something you did not inspect with a command.

4. SAFETY RAILS (deny list)
- Never run: git push, git reset --hard, git clean, git rebase, any history rewrite, git add . / git add -A. Stage explicit paths only. Commit small logical units with conventional messages. Never commit .env, data/, *.sqlite3, .venv, node_modules, reports/.
- Never edit system files or services (pg_hba.conf, registry, Windows services). Never run anything needing admin elevation. Never delete anything outside this repository folder. Never print SECRET_KEY or other secrets.
- The colour palettes in scripts/verify_contrast.py are frozen. That script must exit 0. Do not change palette tokens.

5. ENVIRONMENT
- Windows + PowerShell, Python 3.13.5, virtualenv at .venv, Django 5.2.x LTS (not 6.x). Database: SQLite (decided). No Docker, no HTMX, no Tailwind, no React.
- Write PowerShell-safe commands. Use pathlib and UTF-8. Put anything with nested quotes into a script file under scripts/ instead of a one-liner.
- Test command: python manage.py test --settings=config.settings.test

6. SQLITE RULES (keep the code portable to PostgreSQL later)
- Do not use django.contrib.postgres or any Postgres-only feature.
- SQLite stores decimals as floating point internally. Never Sum/Avg/arithmetic money in SQL. Do all money math in Python Decimal (ROUND_HALF_UP, 2 places). SQL may COUNT, filter and order on money columns.
- select_for_update is a no-op on SQLite. Protect stock and counters with transaction.atomic plus atomic conditional UPDATE statements (UPDATE ... WHERE quantity >= n, check rows affected) and SQLite IMMEDIATE transactions.
- Concurrency tests must use a file-based test database.

7. COMMERCE RULES
- Server-rendered Django is the source of truth. The whole store works with JavaScript disabled.
- All displayed prices are GST-inclusive. Never add GST on top. Extract: tax = price x rate / (100 + rate). The server recalculates everything; never trust client prices, IDs, discounts, stock, payment status, or ownership.
- Order lines snapshot name, SKU, price, MRP, HSN, GST rate and split. Never read the current Product price after an order exists.
- Amazon ratings in the dataset are source data, never store reviews. Never emit Review or AggregateRating schema. Hotlinked images are for development only.
- Bill of Supply mode when SELLER_GSTIN is blank: no GST is charged or displayed, and the document is a Bill of Supply.

8. QUALITY BAR
- Meaningful tests for every service module. No TODOs, pseudocode, or placeholders in committed code. All imports present. Type hints and docstrings on services (state the business rule in the docstring).
- No N+1 queries (select_related / prefetch_related). Add DB constraints and indexes.
- Maintain docs/LEDGER.md (compact): apps, models with key fields, URL names, template names, env vars, business rules. Update it every phase.

9. DESIGN NORTH STAR (so models and templates serve it)
Concept: "The Kinetic Monograph". A warm, tactile, print-publication feel brought to life: stone and clay paper tones, charcoal ink, one deep accent per product category (the ten frozen category colour worlds), a high-character serif for editorial voice (Fraunces) with a clean grotesque for utility (Plus Jakarta Sans), both self-hosted. Marketplace product photos are white-background, so they are blended with multiply onto warm card bases. The store should feel crafted, calm and human: generous whitespace, real typography, honest copy, no marketing claims that are not in the data. Two layers: an editorial layer (homepage, category spreads, product hero) and a calm, dense utility layer (grid, filters, cart, checkout, account). Banned: purple/blue AI gradients, glassmorphism, centred hero with three cards, emoji icons, lorem ipsum, decorative glow or blur, fake reviews/awards/metrics.

10. REPORTING
At the end of each phase write docs/phase-N-report.md and send a final message with these sections: Done / Real command results / Decisions made / Deviations from spec / Known issues / ACTION REQUIRED FROM OWNER (only items that genuinely need me, e.g. SELLER_STATE) / Readiness for next phase.
