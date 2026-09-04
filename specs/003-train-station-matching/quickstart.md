# Quickstart: Train/Station-Based Ride Matching

Validation guide for Feature 003. Assumes Feature 001's API/mobile app are already running
(see `specs/001-ride-pairing-mvp/quickstart.md` for base setup — docker-compose Postgres/PostGIS,
`uvicorn` API, Expo/emulator mobile app).

## Prerequisites

- Feature 001 fully working (verified rider, working OTP flow) — this feature only adds on top.
- `stations` table seeded: run the one-off seed job against the `datameet/railways` dataset
  (see `data-model.md#station-new`; task will be defined in `tasks.md`).
- `TrainDataProvider` configured to `static_fallback` by default; `rapidapi_irctc` is opt-in via
  config/env var once a RapidAPI key is obtained (no key = feature still works, schedule/live
  status simply reports "unavailable").

## Scenario 1: Station autocomplete works offline from any external API

1. `GET /stations/search?q=new+del`
2. **Expect**: 200 with at least "New Delhi (NDLS)" in results, returned with no external network
   call (purely local DB query) — confirms FR-001/FR-002/SC-002.

## Scenario 2: Train route search degrades gracefully with no provider configured

1. With `TrainDataProvider` set to `static_fallback` (default/no API key configured):
   `GET /trains/search?originStationCode=NDLS&destinationStationCode=CSMT&date=2026-09-10`
2. **Expect**: 200 with an empty array or a clear "no data — enter train number manually" signal,
   never a 500 or hang — confirms FR-004/FR-006.
3. Switch config to `rapidapi_irctc` with a valid key and repeat.
4. **Expect**: 200 with a non-empty list of trains (train number, name, times) if the route has
   direct trains — confirms User Story 2 acceptance scenario 1.

## Scenario 3: Live status is always labeled, never silently stale

1. `GET /trains/12951/live-status?date=2026-09-10` with the provider unreachable (e.g., wrong/no
   API key, or throttle the network).
2. **Expect**: 200 with `"available": false` and `"asOf": null` — never a 4xx/5xx, never a fake
   "on time" default — confirms FR-005.
3. Repeat with the provider reachable.
4. **Expect**: `"available": true`, non-null `delayMinutes`/`lastStationCode`/`asOf` — confirms
   the happy path of User Story 3.

## Scenario 4: Two riders on the same train get matched

1. Create two verified riders (A, B) with confirmed ride intents.
2. `POST /intents/{A}/select-train` and `POST /intents/{B}/select-train` with the same
   `trainNumber` and `travelDate`.
3. Trigger the matching cycle (existing job/trigger from Feature 001).
4. `GET` each rider's matches.
5. **Expect**: both riders see a Match with `matchReason: "same_train"` referencing the other —
   confirms FR-007/SC-003.

## Scenario 5: Two riders on different trains arriving close together get matched

1. Create two verified riders (C, D) with ride intents whose `destination_station_id` is the same
   station, and whose selected trains' scheduled (or live, if available) arrival times are within
   the configured window (default 30 min) of each other, but with different `trainNumber`s.
2. Trigger the matching cycle.
3. **Expect**: both riders see a Match with `matchReason: "similar_arrival_time"` and a
   `timingBasis` of `"scheduled"` (or `"live_status"` if live data was fresh) — confirms
   FR-008.

## Scenario 6: A match is invalidated when one side cancels

1. From Scenario 4 or 5, cancel rider A's (or C's) ride intent.
2. `GET` rider B's (or D's) match.
3. **Expect**: the match now has a non-null `invalidatedAt`, and the mobile UI (per spec User
   Story 4 / FR-009) shows it as no longer active rather than leaving a stale "match found" state
   — confirms SC-005.

## Scenario 7: Booking hand-off never implies in-app payment

1. From a confirmed match with a selected train, `GET /matches/{matchId}/booking-link`.
2. **Expect**: 200 with a `bookingUrl` pointing to an external site/deep link and a `disclosure`
   string explicitly stating booking/payment happens outside the app — confirms FR-011 and the
   Constitution Principle IV justification in `plan.md`.

## Mobile (manual) smoke test on the Android emulator

1. Post a ride intent, type a partial station name in the pickup field → suggestions appear
   (Scenario 1's UI counterpart).
2. Select destination station, tap "find trains" → train list appears or a friendly "no trains
   found" message (Scenario 2's UI counterpart).
3. Select a train → live status badge shows either a delay/last-station or a clearly labeled
   "status unavailable" state (Scenario 3's UI counterpart) — never a blank/frozen badge.
4. With a second test rider matched via Scenario 4/5, confirm the Match Review screen shows the
   `matchReason` in plain language ("Same train" / "Arriving around the same time").
