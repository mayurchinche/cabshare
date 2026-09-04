<!--
Sync Impact Report
- Version change: (none) → 1.0.0
- Modified principles: N/A (initial ratification)
- Added sections: Core Principles (6), Technical Constraints, Development Workflow, Governance
- Removed sections: none
- Follow-up TODOs: TODO(RATIFICATION_DATE) — confirm actual founding date if different from today
-->

# CabShare Constitution
<!-- Peer-to-peer, station-to-destination cab pairing app (Android + iOS) -->

## Core Principles

### I. Privacy by Default (NON-NEGOTIABLE)
No two matched riders may ever see each other's phone number, email, exact home/work address,
or any other direct contact identifier at any point in the flow. All in-app communication MUST
go through an anonymized in-app channel or a masked/proxy number. Location shared for matching
is limited to the minimum precision required (pickup/drop geohash, not live continuous tracking
of history). Rationale: contact-detail exposure is the single biggest safety and trust risk for
a stranger-pairing product; violating this is a legal and reputational failure mode, not a bug.

### II. Safety-First Matching
Every user must complete identity verification (phone OTP + selfie/ID check before first ride)
before they can be paired. Matches MUST expose to both riders: verified name (first name +
last initial), photo, rating, and gender preference filter if set. Pairing MUST be cancellable
by either party up to a defined cutoff with no penalty. Rationale: physical co-presence with a
stranger carries real-world risk; verification and mutual visibility are the minimum bar, not a
nice-to-have.

### III. Radius & Matching Integrity
Matching groups riders only within a configurable geo-radius of both pickup and drop points
(default 2 km, tunable per city without a code change). The matching algorithm's radius,
timing window, and max group size MUST be externally configurable (config/DB), never
hardcoded in business logic. Rationale: the right radius differs by city density; baking it
into code guarantees a rewrite the first time it needs tuning.

### IV. Partner-Agnostic Booking Abstraction
Ride booking MUST be implemented behind a single internal `BookingProvider` interface, never
called directly from feature code. The MVP ships with a manual-confirmation provider (user
books via their own Ola/Uber/Rapido app and confirms in-app); no scraping or unofficial API
integration against partner apps is permitted. Automated multi-stop booking via an official
partner/business API MAY be added later as an additional provider behind the same interface,
enabled per-partner via config. Rationale: no aggregator currently exposes a public multi-stop
booking API for third parties — designing for swappable providers now avoids a rewrite later,
without wasting effort building automation that isn't available yet.

### V. Transparent, Simple Monetization
The platform fee is a flat ₹10 per rider per matched ride, shown to the user before they confirm
a match, with no hidden markup on the underlying cab fare. Fare-splitting logic (base fare +
distance-based allocation across stops) MUST be shown as a line-item breakdown, not a single
opaque total. Rationale: users are strangers splitting a ride bill; ambiguity here directly
causes disputes and churn.

### VI. Cross-Platform Parity & MVP Discipline (NON-NEGOTIABLE)
Android and iOS MUST ship with equivalent core functionality from the same release (single
React Native codebase; no platform-exclusive core features). New features start at MVP scope
(YAGNI) — a capability is added only when a real user flow needs it, not speculatively for
"future scale." Every ride-matching, payment, or safety code path MUST have an automated test
before merge; other paths are tested pragmatically. Rationale: a two-sided marketplace dies if
one platform lags, and this is a startup, not a platform for its own sake — speed of learning
beats speculative architecture.

## Technical Constraints

- Mobile: React Native (TypeScript), single codebase for Android + iOS.
- Backend: Python + FastAPI, PostgreSQL with PostGIS for geo-matching queries.
- Booking integrations are additive plugins behind the `BookingProvider` interface (Principle IV);
  no partner integration may bypass it.
- All location and contact data at rest MUST be encrypted; contact-detail masking (Principle I)
  is enforced server-side, never trusted to client-side filtering alone.
- Compliance: platform must support data-deletion-on-request and comply with India's DPDP Act
  (and equivalent regional law before any non-India launch).

## Development Workflow

- Every feature proceeds through `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
  `/speckit-implement`; no direct-to-code changes for new user-facing capability.
- `/speckit-analyze` MUST be run (and CRITICAL findings resolved) before `/speckit-implement`
  on any feature touching matching, payments, or contact-detail handling.
- Code review MUST explicitly check Principle I (no contact leakage) and Principle IV (no
  direct partner-app calls) on any touched file in those areas.

## Governance

This constitution supersedes ad-hoc practices. Amendments require: (1) a documented rationale,
(2) a version bump per semantic versioning (MAJOR = principle removed/redefined, MINOR =
principle added/materially expanded, PATCH = wording/clarification), (3) update of
`LAST_AMENDED_DATE` below. All specs, plans, and PRs are reviewed for compliance with these
principles; unresolved conflicts block merge until the spec/plan/code is adjusted (the
constitution is not diluted to fit existing work). Use `.specify/memory/constitution.md` as the
runtime source of truth for these rules.

**Version**: 1.0.0 | **Ratified**: 2026-08-31 | **Last Amended**: 2026-08-31
