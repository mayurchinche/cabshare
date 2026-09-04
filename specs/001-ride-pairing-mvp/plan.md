# Implementation Plan: Station-to-Destination Ride Pairing (MVP)

**Branch**: `001-ride-pairing-mvp` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ride-pairing-mvp/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Riders arriving at a station post a ride-share intent (destination, luggage size, expected
arrival time) ahead of time. At the rider's expected arrival, the system runs a 5-minute
matching window (PostGIS radius query + overlapping-window filter, first-come-first-served
tie-break) to pair exactly two riders. Both riders review a masked profile, combined stop
order, and a distance-proportional fare-split, then independently confirm before the ride is
marked "ready to book." Actual cab booking is fulfilled manually by the rider through their own
Ola/Uber/Rapido app (MVP `BookingProvider`), confirmed back in-app. No contact details are ever
exposed between matched riders.

## Technical Context

**Language/Version**: TypeScript (React Native 0.74+) for mobile; Python 3.12 for backend

**Primary Dependencies**: React Native + React Navigation (mobile); FastAPI + SQLAlchemy +
GeoAlchemy2 (backend); APScheduler (matching-window trigger + intent expiry); Firebase Cloud
Messaging / APNs (match/cancel push notifications)

**Storage**: PostgreSQL 16 with PostGIS extension (geo radius queries on destination points)

**Testing**: Jest + React Native Testing Library (mobile); pytest + pytest-asyncio (backend);
contract tests against the `/contracts` OpenAPI spec

**Target Platform**: iOS 15+ and Android 8+ (single React Native codebase); backend on a
containerized Linux server

**Project Type**: mobile-app + api (Option 3 — mobile client + backend API)

**Performance Goals**: matching computation completes within the 5-minute window with p95
decision latency <2s per intent; API endpoints p95 <300ms

**Constraints**: contact details (phone/email/exact address) MUST NOT appear in any API response
payload visible to a matched rider (server-side enforced, not client-filtered); intent
submission MUST tolerate brief offline periods (e.g., rider still on a train) via client-side
queue-and-retry

**Scale/Scope**: single-city MVP pilot; design for ~5,000 concurrent open intents and ~20
screens across the one mobile app

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Privacy by Default | Contact fields excluded from all match/ride API schemas at the data-model level (see `data-model.md`); masked-profile view is the only cross-rider projection. | PASS |
| II. Safety-First Matching | Phone OTP + ID/selfie verification gates intent posting; masked profile (name, photo, rating) shown pre-confirmation; mutual independent confirm required. | PASS |
| III. Radius & Matching Integrity | Matching radius (2 km default), window (5 min), and tie-break rule stored as config, not hardcoded; PostGIS `ST_DWithin` parameterized by config value. | PASS |
| IV. Partner-Agnostic Booking Abstraction | Single `BookingProvider` interface; MVP implements only `ManualConfirmationProvider`. No direct/unofficial partner API calls. | PASS |
| V. Transparent Monetization | Fare-split (distance-proportional) and flat ₹10 fee itemized and returned as separate line items in the ride/quote API, not a single total. | PASS |
| VI. Cross-Platform Parity & MVP Discipline | Single React Native codebase for iOS + Android; scope limited to 2-rider MVP per spec assumptions; no speculative multi-rider pooling built now. | PASS |

No violations — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-ride-pairing-mvp/
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
│   ├── models/          # SQLAlchemy models: Rider, RideIntent, Match, Ride
│   ├── services/        # matching_service, fare_service, verification_service,
│   │                     booking/ (BookingProvider interface + ManualConfirmationProvider)
│   ├── api/              # FastAPI routers: intents, matches, rides, riders
│   └── jobs/             # APScheduler jobs: matching-window trigger, intent expiry
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

mobile/
├── src/
│   ├── screens/          # PostIntent, MatchReview, RideConfirm, Cancel, Verification
│   ├── components/
│   ├── services/         # API client, push-notification handling, offline queue
│   └── navigation/
└── tests/
    ├── integration/
    └── unit/
```

**Structure Decision**: Mobile + API split (Option 3). `api/` is the FastAPI + PostgreSQL/PostGIS
backend; `mobile/` is the single React Native codebase shipping both iOS and Android from the
same source, per Constitution Principle VI.

## Complexity Tracking

> No Constitution Check violations — this section intentionally left empty.

