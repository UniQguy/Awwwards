# ELECTROCART Documentation Index

This directory contains the complete technical, design, architectural, and operational documentation for the **ELECTROCART** project.

---

## Core Architecture & Foundations

- [**STANDING_ORDERS.md**](STANDING_ORDERS.md)
  The immutable foundational constraints: zero client-side JavaScript requirement for commerce flows, honest pricing without synthetic scarcity or fake reviews, pure Python GST invoices, and strict design guardrails.

- [**LEDGER.md**](LEDGER.md)
  The canonical single source of truth for all database models, fields, types, financial arithmetic constraints, and service boundaries.

- [**URLS.md**](URLS.md)
  Comprehensive route map of every URL path, view function, template path, authorization rule, and template context contract across the application.

- [**DECISIONS.md**](DECISIONS.md)
  Chronological log of major architectural and design trade-offs, package choices, font selections, and implementation decisions.

- [**KNOWN_ISSUES.md**](KNOWN_ISSUES.md)
  Transparent inventory of technical debt, legacy data anomalies, accepted upstream package constraints, and planned enhancements.

---

## Design System, Copy & Motion

- [**DESIGN_SYSTEM.md**](DESIGN_SYSTEM.md)
  "The Kinetic Monograph": typography scales (Fraunces + Plus Jakarta Sans), 4px spatial grid, 10 frozen category color-worlds, paper-and-ink materiality, and component patterns.

- [**COPY.md**](COPY.md)
  Brand voice, editorial tone, prohibited marketing hype words, microcopy guidelines, and regulatory disclosure language.

- [**MOTION.md**](MOTION.md)
  Progressive enhancement motion tiers (Tier 1: static crossfades; Tier 2: Lenis + GSAP scroll orchestration; Tier 3: Three.js interactive WebGL canvas).

---

## Production Readiness, Security & Operations

- [**ACCESSIBILITY.md**](ACCESSIBILITY.md)
  WCAG 2.1 AA accessibility audit results, high-contrast `@media (forced-colors: active)` mode, touch target compliance ($\ge 44$px), and keyboard focus rings.

- [**PERFORMANCE.md**](PERFORMANCE.md)
  Database query invariants (zero N+1 queries), SQLite connection pragmas (WAL, synchronous=NORMAL), WhiteNoise 1-year immutable caching, and PostgreSQL migration instructions.

- [**SECURITY_REVIEW.md**](SECURITY_REVIEW.md)
  Threat model analysis: price tampering prevention, stock overselling guards, coupon rate limits, IDOR protection, logging PII redaction, and `check --deploy` verification.

- [**ENVIRONMENT.md**](ENVIRONMENT.md)
  Production deployment reference, complete environment variable specification table, cron job schedules, and operational maintenance procedures.

---

## Phase Delivery Reports

- [**Phase 1 Report: Foundation & Catalog**](phase-1-report.md)
- [**Phase 2 Report: The Commerce Engine**](phase-2-report.md)
- [**Phase 3 Report: The Working Storefront (Zero JS)**](phase-3-report.md)
- [**Phase 4 Report: Design System & Utility Layer**](phase-4-report.md)
- [**Phase 5 Report: The Editorial Layer**](phase-5-report.md)
- [**Phase 6 Report: Motion & WebGL Progressive Enhancement**](phase-6-report.md)
- [**Phase 7 Report: Hardening, Polish & Launch Preparation**](phase-7-report.md)
- [**Final Delivery Report & Owner Actions**](FINAL_REPORT.md)
