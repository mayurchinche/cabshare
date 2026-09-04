# Tasks: Train/Station-Based Ride Matching

**Input**: Design documents from `/specs/003-train-station-matching/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Not explicitly requested in the spec beyond the quickstart scenarios; contract/unit test
tasks are included only where the Constitution mandates them (matching/payments/contact-detail
paths — Development Workflow rule) or where research.md flags a reliability-critical fallback.

**Organization**: Tasks are grouped by user story (US1-US5) per spec.md priorities.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Add `httpx` to `api/requirements.txt` (or `pyproject.toml`, matching existing convention) for outbound `TrainDataProvider` calls
- [ ] T002 [P] Add Alembic migration in `api/src/migrations/versions/` for new tables: `stations`, `trains`, `train_live_status_cache`, plus new columns on `ride_intents` (`origin_station_id`, `destination_station_id`, `selected_train_id`, `travel_date`) and `matches` (`match_reason`, `timing_basis`, `invalidated_at`)
- [ ] T003 [P] Add `TRAIN_DATA_PROVIDER` config (`static_fallback` default, `rapidapi_irctc` opt-in) and `SIMILAR_ARRIVAL_WINDOW_MINUTES` (default 30) and `LIVE_STATUS_FRESHNESS_MINUTES` (default 15) to `api/src/config.py`

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `Station` model in `api/src/models/station.py` per data-model.md (station_code, name, state, city, location geography point, source_dataset_version)
- [ ] T005 Create `Train` model in `api/src/models/train.py` per data-model.md (train_number, train_name, route JSON, provider_source, cached_at)
- [ ] T006 Create `TrainLiveStatusCache` model in `api/src/models/train_live_status_cache.py` per data-model.md
- [ ] T007 Extend `RideIntent` model in `api/src/models/ride_intent.py` with `origin_station_id`, `destination_station_id`, `selected_train_id`, `travel_date` (FKs/nullable per data-model.md)
- [ ] T008 Extend `Match` model in `api/src/models/match.py` with `match_reason`, `timing_basis`, `invalidated_at` (defaulting `match_reason="geo_radius"` for existing rows)
- [ ] T009 Create `TrainDataProvider` ABC in `api/src/services/train_data/base.py` (mirrors `api/src/services/booking/base.py` pattern): `search_trains(origin_code, dest_code, date) -> list[Train]`, `get_live_status(train_number, date) -> TrainLiveStatus`
- [ ] T010 [P] Implement `static_fallback` provider in `api/src/services/train_data/static_fallback.py` (returns empty train list / `available=False` status, zero external calls)
- [ ] T011 Write one-off seed script in `api/src/jobs/seed_stations_job.py` to import the `datameet/railways` station GeoJSON dataset into the `stations` table (idempotent, safe to re-run)

**Checkpoint**: Foundation ready — user stories can now be implemented

---

## Phase 3: User Story 1 - Pick locations as railway stations (Priority: P1) 🎯 MVP

**Goal**: Riders search and select pickup/destination as canonical stations instead of free text.

**Independent Test**: Per quickstart.md Scenario 1 — `GET /stations/search?q=new+del` returns
matching stations from local DB with no external call.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `station_service.search(query, near=None)` in `api/src/services/station_service.py` (prefix/trigram search over `stations.name`, optional proximity sort via `location`)
- [ ] T013 [US1] Add `GET /stations/search` router in `api/src/api/stations.py` per contracts/train-station-api.yaml, wired into `api/src/main.py`
- [ ] T014 [P] [US1] Add `Station` response schema in `api/src/api/schemas/station.py`
- [ ] T015 [P] [US1] Create `StationAutocomplete` component in `mobile/src/components/StationAutocomplete.tsx` (debounced search-as-you-type, min 3 chars, calls new station API)
- [ ] T016 [US1] Add `searchStations()` to `mobile/src/services/stationApi.ts`
- [ ] T017 [US1] Wire `StationAutocomplete` into pickup/destination fields in `mobile/src/screens/PostIntent.tsx`, replacing free-text inputs, storing the selected `stationCode`

**Checkpoint**: US1 fully functional and independently testable (quickstart Scenario 1)

---

## Phase 4: User Story 2 - See trains running on the chosen route (Priority: P1)

**Goal**: Once both stations are picked, show trains running that route.

**Independent Test**: Per quickstart.md Scenario 2 — `GET /trains/search` returns a list (or a
clear empty/error state) for a station pair, working with both `static_fallback` and
`rapidapi_irctc` providers.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `rapidapi_irctc` provider in `api/src/services/train_data/rapidapi_irctc.py` (`search_trains` + `get_live_status`, timeout + no aggressive retry per plan.md Constraints, credentials via config)
- [ ] T019 [US2] Implement `train_search_service.search(origin, dest, date)` in `api/src/services/train_data_service.py`: calls configured `TrainDataProvider`, persists/reuses cached rows in `trains` table
- [ ] T020 [US2] Add `GET /trains/search` router in `api/src/api/trains.py` per contracts/train-station-api.yaml (503 on provider failure per contract, never 500)
- [ ] T021 [P] [US2] Add `Train` response schema in `api/src/api/schemas/train.py`
- [ ] T022 [US2] Add `POST /intents/{intentId}/select-train` endpoint in `api/src/api/intents.py` (sets `selected_train_id` + `travel_date`, validates intent not already matched/cancelled per contract's 409 case)
- [ ] T023 [P] [US2] Add `searchTrains()` and `selectTrain()` to `mobile/src/services/trainApi.ts`
- [ ] T024 [P] [US2] Create `TrainListCard` component in `mobile/src/components/TrainListCard.tsx` (train number/name/times, tap to select)
- [ ] T025 [US2] Wire train search + selection into `mobile/src/screens/PostIntent.tsx` after both stations are chosen, including a friendly "no direct trains found" empty state and a manual train-number fallback entry when the provider is unavailable (FR-006)

**Checkpoint**: US1 + US2 both independently functional (quickstart Scenarios 1-2)

---

## Phase 5: User Story 4 - Match with co-passengers on the same or arriving train (Priority: P1)

**Goal**: Riders on the same train, or different trains arriving close together, see each other as matches.

**Independent Test**: Per quickstart.md Scenarios 4-6 — two riders on the same train/date match
with reason `same_train`; two riders arriving within the configured window match with reason
`similar_arrival_time`; cancelling one side sets `invalidated_at` on the other's match.

> **Note**: Implemented before User Story 3 (live status) because matching must work correctly
> using scheduled times alone per FR-006/Constraints — live status (US3) only enriches the timing
> basis, it is not a prerequisite.

### Implementation for User Story 4

- [ ] T026 [US4] Extend `matching_service` in `api/src/services/matching_service.py` with a `same_train` strategy: exact `selected_train_id` + `travel_date` match → create/associate `Match` with `match_reason="same_train"`
- [ ] T027 [US4] Extend `matching_service` in `api/src/services/matching_service.py` with a `similar_arrival_time` strategy: same `destination_station_id`, arrival time delta within `SIMILAR_ARRIVAL_WINDOW_MINUTES` (using live status if fresher than `LIVE_STATUS_FRESHNESS_MINUTES`, else scheduled) → create/associate `Match` with `match_reason="similar_arrival_time"` and correct `timing_basis`
- [ ] T028 [US4] Add match-invalidation logic in `api/src/services/matching_service.py` (or `api/src/jobs/intent_expiry_job.py` if cancellation is event-driven there): on `RideIntent` cancellation, set `invalidated_at` on any associated `Match` (FR-009)
- [ ] T029 [P] [US4] Extend `Match` response schema in `api/src/api/schemas/match.py` with `matchReason`, `timingBasis`, `invalidatedAt` fields per contracts/train-station-api.yaml
- [ ] T030 [US4] Update `mobile/src/screens/MatchReview.tsx` to render `matchReason` in plain language ("Same train" / "Arriving around the same time") and visually flag matches with a non-null `invalidatedAt` as no longer active
- [ ] T031 [P] [US4] Add a designed empty state (using Feature 002's `EmptyState` component if already available, else a plain interim empty view) to `mobile/src/screens/MatchReview.tsx` for the zero-matches case (FR-010 cross-reference)

**Checkpoint**: US1, US2, US4 deliver the full core "pick station → find train → get matched" loop

---

## Phase 6: User Story 3 - Live running status of the chosen train (Priority: P2)

**Goal**: Show best-effort live delay/last-station for a selected train; never block on it.

**Independent Test**: Per quickstart.md Scenario 3 — live-status endpoint always returns 200,
`available:false` when the provider fails, `available:true` with data when it succeeds.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `get_live_status(train_number, date)` in `api/src/services/train_data_service.py`: calls configured provider with short timeout, reads/writes `train_live_status_cache`, always returns a `TrainLiveStatus` object (never raises to the caller — catches provider errors and returns `available=False`)
- [ ] T033 [US3] Add `GET /trains/{trainNumber}/live-status` router in `api/src/api/trains.py` per contracts/train-station-api.yaml
- [ ] T034 [P] [US3] Add `TrainLiveStatus` response schema in `api/src/api/schemas/train.py`
- [ ] T035 [P] [US3] Add `getLiveStatus()` to `mobile/src/services/trainApi.ts`
- [ ] T036 [P] [US3] Create `LiveStatusBadge` component in `mobile/src/components/LiveStatusBadge.tsx` (shows delay + last station + "as of [time]", or a clearly labeled "unavailable" state)
- [ ] T037 [US3] Wire `LiveStatusBadge` into the selected-train view in `mobile/src/screens/PostIntent.tsx`

**Checkpoint**: All P1+P2 stories functional independently and together

---

## Phase 7: User Story 5 - Proceed to book the train (Priority: P3)

**Goal**: Hand off to an external booking flow with train/date/stations pre-filled.

**Independent Test**: Per quickstart.md Scenario 7 — `GET /matches/{matchId}/booking-link`
returns a `bookingUrl` + explicit non-in-app-payment `disclosure` string.

### Implementation for User Story 5

- [ ] T038 [US5] Extend `api/src/services/booking/base.py`'s usage (or add a small standalone `booking_link_service.py` if a full `BookingProvider` is overkill for a static deep link) to build an IRCTC/third-party deep link pre-filled with train number, date, station codes
- [ ] T039 [US5] Add `GET /matches/{matchId}/booking-link` router in `api/src/api/matches.py` per contracts/train-station-api.yaml, always including the payment-disclosure string (FR-011)
- [ ] T040 [P] [US5] Add `getBookingLink()` to `mobile/src/services/trainApi.ts`
- [ ] T041 [US5] Add a "Book this train" button + disclosure text to `mobile/src/screens/RideConfirm.tsx`, opening the returned `bookingUrl` externally (`Linking.openURL`)

**Checkpoint**: All five user stories independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T042 [P] Add a fake in-memory `TrainDataProvider` in `api/tests/contract/fakes/fake_train_data_provider.py` for deterministic contract tests (no real network calls in CI, per plan.md Testing strategy)
- [ ] T043 [P] Add contract tests for `/stations/search`, `/trains/search`, `/trains/{trainNumber}/live-status`, `/intents/{intentId}/select-train`, `/matches/{matchId}/booking-link` in `api/tests/contract/test_train_station_api.py`, since matching-adjacent endpoints fall under the Constitution's "matching...code path MUST have an automated test before merge" rule
- [ ] T044 [P] Add unit tests for the `same_train` and `similar_arrival_time` matching strategies in `api/tests/unit/test_matching_service_train.py` (Constitution: matching code paths must have automated tests)
- [ ] T045 Run `specs/003-train-station-matching/quickstart.md` end-to-end on the Android emulator and record results
- [ ] T046 Run `/speckit-analyze` and resolve any CRITICAL findings before considering this feature done (Constitution Development Workflow rule — this feature touches matching)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **US1 (Phase 3)**: Depends on Foundational only.
- **US2 (Phase 4)**: Depends on Foundational + US1 (needs station codes to search trains).
- **US4 (Phase 5)**: Depends on Foundational + US2 (needs `selected_train_id`/`travel_date` on intents to match on). Implemented before US3 since matching must work on schedule alone.
- **US3 (Phase 6)**: Depends on Foundational + US2 (needs a selected train to check status for); independent of US4 — could be built in parallel with Phase 5 by a second developer.
- **US5 (Phase 7)**: Depends on US4 (needs a confirmed `Match`) and US2 (needs `selected_train_id`).
- **Polish (Phase 8)**: Depends on all desired stories being complete.

### Parallel Opportunities

- T002, T003 (Setup) in parallel.
- T010 (Foundational) in parallel with T004-T009 once models are stubbed.
- Within US1: T012, T014, T015 in parallel; T013/T016/T017 depend on those.
- Within US2: T018, T021, T023, T024 in parallel; T019/T020/T022/T025 depend on those.
- US3 (Phase 6) can proceed in parallel with US4 (Phase 5) once US2 is done — different files, no shared state beyond the `Train`/cache models already created in Foundational.
- T042-T044 (Polish) in parallel.

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 4)

1. Setup + Foundational.
2. US1 (station picker) → validate independently.
3. US2 (train search) → validate independently.
4. US4 (same-train / similar-arrival matching) → validate independently — **this is the demoable
   core loop** ("pick stations → see trains → get matched"), even without live status or booking.
5. Demo/ship here if time-constrained; US3 and US5 are additive enhancements, not required for the
   core value proposition to be demonstrable.

### Incremental Delivery

Setup+Foundational → US1 → US2 → US4 (core loop demoable) → US3 (adds live status) → US5 (adds
booking hand-off) → Polish.
