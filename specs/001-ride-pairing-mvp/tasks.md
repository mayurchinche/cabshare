---

description: "Task list for Station-to-Destination Ride Pairing (MVP)"
---

# Tasks: Station-to-Destination Ride Pairing (MVP)

**Input**: Design documents from `/specs/001-ride-pairing-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ride-pairing-api.yaml, quickstart.md

**Tests**: Spec does not request full TDD. Per the project constitution, matching, fare-split
(payment-adjacent), and verification (safety) code paths MUST have automated tests before merge
— those are included below. Other paths are tested pragmatically (contract/integration tests
in the Polish phase) rather than exhaustively unit-tested.

**Organization**: Tasks are grouped by user story (US1/US2/US3, matching spec.md priorities P1/P2/P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 (post intent + pairing), US2 (review + confirm), US3 (cancel)

## Path Conventions

Mobile + API split per plan.md: `api/src/`, `api/tests/`, `mobile/src/`, `mobile/tests/`.

---

## Phase 1: Setup

- [X] T001 Create repository structure per plan.md: `api/src/{models,services,api,jobs}`,
      `api/tests/{contract,integration,unit}`, `mobile/src/{screens,components,services,navigation}`,
      `mobile/tests/{integration,unit}`
- [X] T002 Initialize `api/` as a Python 3.12 project with FastAPI, SQLAlchemy, GeoAlchemy2,
      APScheduler, pytest, pytest-asyncio in `api/pyproject.toml`
- [X] T003 Initialize `mobile/` as a React Native 0.74+ TypeScript project with React Navigation,
      Jest, React Native Testing Library in `mobile/package.json`
- [X] T004 [P] Configure linting/formatting: ruff + black for `api/` (`api/pyproject.toml`),
      eslint + prettier for `mobile/` (`mobile/.eslintrc.js`)
- [X] T005 [P] Add local dev DB setup: PostgreSQL 16 + PostGIS via `docker-compose.yml` at repo
      root, with a `postgis` service and healthcheck
- [X] T006 Set up Alembic migrations scaffold in `api/src/migrations/` wired to the SQLAlchemy
      models package

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Core infrastructure every user story depends on. No user story is testable until
this phase is complete.

- [X] T007 Create `Rider` model with `verification_status`, `display_name`, `photo_url`,
      `rating`, `gender` fields (excluding raw contact fields from any shared schema) in
      `api/src/models/rider.py`, per data-model.md
- [X] T008 [P] Create app config module for tunable matching parameters (radius default 2km,
      matching window 5min, cancellation cutoff 10min) sourced from environment/DB in
      `api/src/config.py`, per Constitution Principle III
- [X] T009 [P] Implement `MaskedRiderProfile` Pydantic schema (display_name, photo_url, rating
      only — no phone/email) in `api/src/api/schemas/rider.py`, per contracts/ride-pairing-api.yaml
- [X] T010 [P] Implement verification service (phone OTP + photo/ID check stub) that gates
      `verification_status` transitions in `api/src/services/verification_service.py`
- [X] T011 [P] **Test**: verification service unit test asserting an unverified rider cannot post
      or accept an intent in `api/tests/unit/test_verification_service.py`
- [X] T012 Define `BookingProvider` abstract interface (`book(stop_order, fare_split) -> Ride`)
      in `api/src/services/booking/base.py`, per Constitution Principle IV
- [X] T013 [P] Implement `ManualConfirmationProvider` (records rider's manual booking
      confirmation; no external API calls) in `api/src/services/booking/manual_confirmation.py`
- [X] T014 Wire FastAPI app instance, DB session dependency, and router registration in
      `api/src/main.py`
- [X] T015 [P] Scaffold React Navigation stack (Verification, PostIntent, MatchReview,
      RideConfirm, Cancel screens as placeholders) in `mobile/src/navigation/AppNavigator.tsx`
- [X] T016 [P] Implement API client base (auth header, base URL, offline queue for POST
      `/intents` per plan.md's offline-tolerance constraint) in `mobile/src/services/apiClient.ts`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Post a ride intent and get paired (Priority: P1) 🎯 MVP

**Goal**: A verified rider posts an intent; when a compatible rider is also active, both get
paired within the 5-minute matching window that opens at expected arrival time.

**Independent Test**: Two verified test accounts post compatible intents from the same station
within the matching window; both receive a match with masked profile, combined route, and
fare-split preview (per quickstart.md steps 1–2).

- [X] T017 [US1] Create `RideIntent` model (origin_station, destination + geo point,
      luggage_size, expected_arrival_time, gender_preference, status, matching window
      timestamps) in `api/src/models/ride_intent.py`, per data-model.md
- [X] T018 [US1] Create `Match` model (intent_a_id, intent_b_id, combined_stop_order,
      fare_split, status, confirmation fields) in `api/src/models/match.py`, per data-model.md
- [X] T019 [P] [US1] Implement fare-split service computing distance-proportional shares (base
      fare + platform fee ₹10/rider) in `api/src/services/fare_service.py`
- [X] T020 [P] [US1] **Test**: fare_service unit test asserting unequal stop distances produce
      unequal (non-50/50) shares in `api/tests/unit/test_fare_service.py`
- [X] T021 [US1] Implement matching service: PostGIS `ST_DWithin` radius query + overlapping
      departure-window filter + first-come-first-served tie-break, producing a proposed `Match`
      in `api/src/services/matching_service.py`
- [X] T022 [P] [US1] **Test**: matching_service unit test with 3+ compatible intents asserting
      the two earliest-created are paired first (clarified Q5) in
      `api/tests/unit/test_matching_service.py`
- [X] T023 [US1] Implement APScheduler job that opens each intent's 5-minute matching window at
      `expected_arrival_time` and invokes matching_service in `api/src/jobs/matching_window_job.py`
- [X] T024 [US1] Implement APScheduler job that expires intents whose matching window closed
      with no match (FR-002b/FR-010) in `api/src/jobs/intent_expiry_job.py`
- [X] T025 [US1] Implement `POST /intents` and `GET /intents/{intentId}` endpoints in
      `api/src/api/intents.py`, per contracts/ride-pairing-api.yaml
- [X] T026 [US1] Implement `POST /intents/{intentId}/research` manual re-search endpoint in
      `api/src/api/intents.py`
- [X] T027 [P] [US1] **Test**: contract test for `POST /intents` and `GET /intents/{id}`
      asserting response schema matches contracts/ride-pairing-api.yaml in
      `api/tests/contract/test_intents_contract.py`
- [X] T028 [US1] Build PostIntent screen (destination, luggage size, expected arrival time
      inputs; offline-queued submit) in `mobile/src/screens/PostIntent.tsx`
- [X] T029 [US1] Build intent-status polling/push-listener hook showing "waiting", "matched", or
      "no match — retry/solo" states in `mobile/src/services/intentStatus.ts`

**Checkpoint**: User Story 1 fully functional and independently testable/demoable.

---

## Phase 4: User Story 2 - Review match and confirm shared ride (Priority: P2)

**Goal**: Both matched riders see masked profile, combined stops, itemized fare-split, and must
both independently confirm before the ride is "ready to book."

**Independent Test**: Advance two matched test accounts to confirmation; verify ride only
reaches "ready" after both confirm, and expires if either doesn't respond in time (quickstart.md
step 3).

- [X] T030 [US2] Create `Ride` model (stop_order, fare_split, booking_provider, status,
      cancellation_cutoff_at) in `api/src/models/ride.py`, per data-model.md
- [X] T031 [US2] Implement confirmation logic in matching_service: record
      `rider_a_confirmed_at`/`rider_b_confirmed_at`, transition `Match.status` to `confirmed`
      only when both are set, and create the `Ride` (via `BookingProvider`) on confirmation in
      `api/src/services/matching_service.py`
- [X] T032 [P] [US2] **Test**: matching_service unit test asserting `Match.status` stays
      `proposed` after only one rider confirms in `api/tests/unit/test_match_confirmation.py`
- [X] T033 [US2] Implement match-expiry handling: if `confirmation_deadline` passes without both
      confirmations, cancel the match and return both intents to `open` in
      `api/src/services/matching_service.py`
- [X] T034 [US2] Implement `GET /matches/{matchId}`, `POST /matches/{matchId}/confirm`, and
      `POST /matches/{matchId}/decline` endpoints in `api/src/api/matches.py`, per
      contracts/ride-pairing-api.yaml
- [X] T035 [P] [US2] **Test**: contract test asserting `Match`/`MaskedRiderProfile` API
      responses never contain `phone_number` or `email` fields in
      `api/tests/contract/test_no_contact_leak.py`
- [X] T036 [US2] Implement push notification dispatch (FCM/APNs) on match-proposed and
      match-confirmed events in `api/src/services/notification_service.py`
- [X] T037 [US2] Build MatchReview screen (masked partner profile, combined stop order, itemized
      fare-split with confirm/decline actions) in `mobile/src/screens/MatchReview.tsx`
- [X] T038 [US2] Build RideConfirm screen showing "ready to book" state and manual booking
      hand-off (open partner cab app, confirm booked) in `mobile/src/screens/RideConfirm.tsx`

**Checkpoint**: User Stories 1 AND 2 fully functional together.

---

## Phase 5: User Story 3 - Cancel a pairing before ride start (Priority: P3)

**Goal**: Either rider can cancel a proposed or confirmed pairing; free before the 10-minute
cutoff, fee shown if inside it; the other rider is notified without attribution.

**Independent Test**: Cancel a confirmed pairing before/after the cutoff and verify fee behavior
and other-rider notification (quickstart.md step 4).

- [X] T039 [US3] Implement cancellation logic: compute `within_free_cutoff` from
      `cancellation_cutoff_at`, apply fee if inside the 10-minute window, transition `Ride`/
      `Match` to `cancelled` in `api/src/services/matching_service.py`
- [X] T040 [P] [US3] **Test**: unit test asserting `fee_charged: 0` before cutoff and nonzero
      after, in `api/tests/unit/test_cancellation.py`
- [X] T041 [US3] Implement `POST /rides/{rideId}/cancel` endpoint returning
      `CancellationResult` in `api/src/api/rides.py`, per contracts/ride-pairing-api.yaml
- [X] T042 [US3] Notify the non-cancelling rider (push notification, no attribution of who
      cancelled) and surface rebook-solo/re-match options in
      `api/src/services/notification_service.py`
- [X] T043 [US3] Build Cancel screen/flow (confirm cancellation, show fee if applicable) in
      `mobile/src/screens/Cancel.tsx`
- [X] T044 [US3] Handle the notified rider's rebook-solo / re-match prompt in
      `mobile/src/screens/RideConfirm.tsx`

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T045 [P] Run the quickstart.md end-to-end scenario against a local stack and fix any gaps
      between contract and implementation
- [X] T046 [P] Add structured logging (no PII/contact fields logged) across
      `api/src/services/*.py`
- [X] T047 [P] Mobile integration test covering PostIntent → MatchReview → RideConfirm happy
      path in `mobile/tests/integration/rideFlow.test.tsx`
- [X] T048 Review all API response schemas one more time against Constitution Principle I (no
      contact-detail exposure) before merge

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)**: strictly sequential; nothing else starts
  before Phase 2 completes.
- **Phase 3 (US1)**: depends only on Phase 2. This is the MVP — deliverable and demoable alone.
- **Phase 4 (US2)**: depends on Phase 3 (`Match` records and matching flow must exist).
- **Phase 5 (US3)**: depends on Phase 4 (`Ride`/confirmed `Match` must exist to cancel).
- **Phase 6 (Polish)**: depends on all prior phases.

## Parallel Execution Examples

- Within Phase 2: T008, T009, T010/T011, T013, T015, T016 can run in parallel (different files);
  T007 and T012 and T014 are prerequisites for several of them, so complete those first.
- Within Phase 3: T019/T020 (fare service) and T021/T022 (matching service) touch different
  files and can run in parallel; T025–T027 (endpoints/contract test) depend on T017/T018/T021.
- Within Phase 4: T032 and T035 (tests) can run in parallel once T030/T031/T034 exist.

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**: posting an intent and getting paired is
the smallest slice that proves the core value loop. Ship and validate this before building
confirmation (US2) and cancellation (US3) — each subsequent phase is an incremental,
independently testable delivery on top of the last.
