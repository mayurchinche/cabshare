# Implementation Plan: Train/Station-Based Ride Matching

**Branch**: `003-train-station-matching` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-train-station-matching/spec.md`

## Summary

Riders select pickup/destination as canonical railway stations (via a self-hosted static
station dataset), see trains running that route, and optionally check a train's live running
status (best-effort, degrades to schedule-only when unavailable). Matching is extended with two
new reasons: "same train" (exact train number + date match) and "similar arrival time" (different
trains, same destination station, arrival within a configurable window using live status when
available, else scheduled time). Booking is a hand-off deep link (IRCTC/third-party), never an
in-app transaction. All external train-data lookups (route search, live status) go behind a new
`TrainDataProvider` interface — mirroring the existing `BookingProvider` pattern — so the
unofficial/rate-limited nature of India's train APIs never leaks into matching or UI code and can
be swapped/disabled per Constitution Principle IV's spirit.

## Technical Context

**Language/Version**: TypeScript (React Native 0.81) for mobile; Python 3.12 for backend (same as Feature 001)

**Primary Dependencies**: FastAPI + SQLAlchemy + GeoAlchemy2 (backend, existing); `httpx` (outbound
calls to train-data provider, with timeout + circuit breaker); React Native (existing) + a
lightweight autocomplete component for station search

**Storage**: PostgreSQL 16/PostGIS (existing). New tables: `stations` (seeded once from the
`datameet/railways` CC0 GeoJSON dataset, not fetched live), `trains` (route reference data, cached
from provider responses), `train_live_status_cache` (short-TTL cache of provider live-status
responses, keyed by train number + date, to survive provider rate limits)

**Testing**: pytest + pytest-asyncio (backend, existing); Jest + RNTL (mobile, existing); contract
tests against `/contracts` OpenAPI spec, including a fake `TrainDataProvider` for deterministic
tests (no real network calls in CI)

**Target Platform**: iOS 15+ and Android 8+ (existing React Native app); backend on existing
containerized Linux server

**Project Type**: mobile-app + api (extends Feature 001's structure, no new project)

**Performance Goals**: station autocomplete p95 <300ms (local DB query, no external call); train
route lookup p95 <2s (external provider call, cached); live-status calls MUST NOT block ride-intent
submission (fire-and-forget / background refresh only)

**Constraints**: system MUST function correctly (station selection, train search, "same train"
matching) with the live-status provider fully unavailable — live status is enhancement-only, never
a hard dependency; all outbound calls to the unofficial train-data provider MUST have a timeout and
MUST NOT be retried aggressively (respect rate limits, cache aggressively)

**Scale/Scope**: same single-city MVP pilot scope as Feature 001; station dataset is nationwide
(~8,000 Indian stations) but matching/query scope stays local to the pilot city's relevant stations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Privacy by Default | Match payloads for "same train"/"similar arrival time" reasons carry only first name/initials, train number, timing — no contact details, same schema discipline as Feature 001. | PASS |
| II. Safety-First Matching | This feature only adds a new matching *input* (train/station) and *reason*; existing verification/masked-profile/mutual-confirm flow from Feature 001 is unchanged and still required before any match is shown. | PASS |
| III. Radius & Matching Integrity | New "similar arrival time" window (default 30 min) is externally configurable (DB/config), not hardcoded, matching the existing radius/window config pattern. | PASS |
| IV. Partner-Agnostic Booking Abstraction | Booking hand-off uses a deep link only (no automated booking API call), consistent with "no scraping/unofficial API integration for booking." **However**, train *route search* and *live status* have no official free Indian API — see below. | **NEEDS JUSTIFICATION** |
| V. Transparent, Simple Monetization | No fare/fee model changes; existing ₹10 flat fee and fare-split display logic untouched by this feature. | PASS |
| VI. Cross-Platform Parity & MVP Discipline | Single React Native codebase; station/train features ship on both platforms simultaneously; live-status is explicitly scoped as best-effort/optional per YAGNI (schedule-only is the safe default). | PASS |

**Justification for Principle IV flag**: Principle IV's non-negotiable clause is scoped to *cab
booking fulfillment* ("no scraping or unofficial API integration against partner apps"). Train
route/live-status data is a different domain (public transit schedule data, not a booking
transaction), and no official free Indian Railways API exists for it (confirmed via research —
see `research.md`). To stay in the spirit of the principle, this plan isolates all such calls
behind a single `TrainDataProvider` interface (mirroring `BookingProvider`), never called directly
from matching/UI code, with mandatory graceful degradation when the provider is unavailable. See
Complexity Tracking below.

## Project Structure

### Documentation (this feature)

```text
specs/003-train-station-matching/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
api/
├── src/
│   ├── models/            # + Station, Train, TrainLiveStatusCache (new); RideIntent, Match extended
│   ├── services/
│   │   ├── train_data/    # NEW: TrainDataProvider interface (base.py) + provider impls
│   │   │   ├── base.py            # TrainDataProvider ABC: search_trains(), get_live_status()
│   │   │   ├── rapidapi_irctc.py  # Best-effort unofficial provider (rate-limited, cached)
│   │   │   └── static_fallback.py # Schedule-only provider (no live status), used when disabled
│   │   ├── station_service.py     # NEW: station search/autocomplete over local `stations` table
│   │   ├── matching_service.py    # extended: "same train" / "similar arrival time" reasons
│   │   └── booking/               # existing, extended: pre-fill deep link with train/date/stations
│   ├── api/                # + routers: stations (search), trains (route search, live status)
│   └── jobs/                # + one-off seed job: load datameet/railways dataset into `stations`
└── tests/
    ├── contract/           # + fake TrainDataProvider for deterministic contract tests
    ├── integration/
    └── unit/

mobile/
├── src/
│   ├── screens/            # PostIntent extended: station picker, train list, live status
│   ├── components/         # + StationAutocomplete, TrainListCard, LiveStatusBadge
│   ├── services/           # + stationApi.ts, trainApi.ts
│   └── navigation/
└── tests/
    ├── integration/
    └── unit/
```

**Structure Decision**: Extends Feature 001's existing mobile + API split (Option 3) — no new
top-level project. New backend concerns live under `api/src/services/train_data/` (provider
abstraction) and `api/src/services/station_service.py`; new mobile concerns are additive
components/screens inside the existing `mobile/src/` tree.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Calling an unofficial (non-partner-authorized) train-data API from `TrainDataProvider` | No official free Indian Railways API for train-route-search or live-status exists (confirmed by research); the feature's core value (train/station matching) is impossible without some route+timing data source. | A fully official alternative doesn't exist at any price point accessible to this MVP; waiting for one blocks the feature indefinitely. Mitigated by: (1) isolating all calls behind one swappable interface, (2) a `static_fallback` provider that ships first (schedule-only, zero external calls) so the feature works with zero legal/ToS exposure, (3) the unofficial provider is opt-in/config-gated and never required for core matching to function. |
