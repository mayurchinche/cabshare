# Quickstart: Validate Ride Pairing (MVP) End-to-End

## Prerequisites

- PostgreSQL 16 with PostGIS extension enabled, running locally or in a dev container
  (`docker compose up -d` at the repo root)
- Backend (`api/`) installed and runnable: `pip install -e "./api[dev]"`
- Two verified test rider accounts (`rider_a`, `rider_b`) — verification stubbed/mocked in dev;
  each rider is identified by the `X-Rider-Id: <uuid>` header (MVP auth stand-in, see
  `api/src/api/deps.py` — swap for real auth without touching endpoint logic)
- Backend dev server running: `uvicorn api.src.main:app --reload`

## Scenario: Two riders get paired, confirm, and one cancels late

This walks through User Stories 1–3 from `spec.md` using the contract in
`contracts/ride-pairing-api.yaml`. Verified end-to-end via `api/tests/contract/` (SQLite) —
run `pytest api/tests` to exercise the same flow automatically.

1. **Post two compatible intents** (same station, destinations within 2 km, overlapping
   `expected_arrival_time`, both a few minutes in the future so the matching window opens soon):

   ```bash
   curl -X POST http://localhost:8000/intents \
     -H 'Content-Type: application/json' -H "X-Rider-Id: $RIDER_A_ID" \
     -d '{"origin_station":"Pune Junction","origin_lat":18.5286,"origin_lng":73.8744,"destination":"Baner","destination_lat":18.5590,"destination_lng":73.7868,"luggage_size":"small","expected_arrival_time":"<now+2min>"}'

   curl -X POST http://localhost:8000/intents \
     -H 'Content-Type: application/json' -H "X-Rider-Id: $RIDER_B_ID" \
     -d '{"origin_station":"Pune Junction","origin_lat":18.5286,"origin_lng":73.8744,"destination":"Baner Road","destination_lat":18.5595,"destination_lng":73.7870,"luggage_size":"none","expected_arrival_time":"<now+2min>"}'
   ```

   **Expected**: both return `201` with `status: "open"` and a `matching_window_opens_at` equal
   to their `expected_arrival_time`.

2. **Wait until the matching window opens**, then poll each intent:

   ```bash
   curl http://localhost:8000/intents/<intent_a_id> -H "X-Rider-Id: $RIDER_A_ID"
   ```

   **Expected**: within the 5-minute window (once the background `matching_window_job`, T023, ticks), both intents transition to `status: "matched"` with
   a shared `match_id`. Verifies FR-002/FR-002a and the matching-service tie-break logic.

3. **Fetch the match and confirm both sides**:

   ```bash
   curl http://localhost:8000/matches/<match_id> -H "X-Rider-Id: $RIDER_A_ID"
   ```

   **Expected**: response includes `partner_profile` (display name, photo, rating only — no
   phone/email fields present anywhere in the payload), `combined_stop_order`, and an itemized
   `fare_split` (`your_share`, `partner_share`, `platform_fee_per_rider: 10`) that is not a flat
   50/50 split when stop distances differ. This validates FR-003, FR-004, FR-006.

   ```bash
   curl -X POST http://localhost:8000/matches/<match_id>/confirm -H "X-Rider-Id: $RIDER_A_ID"
   curl -X POST http://localhost:8000/matches/<match_id>/confirm -H "X-Rider-Id: $RIDER_B_ID"
   ```

   **Expected**: match status becomes `confirmed` only after *both* calls succeed (confirming
   after only one call still shows `proposed`). Validates FR-005.

4. **Cancel outside the free window, then inside it**:

   ```bash
   curl -X POST http://localhost:8000/rides/<ride_id>/cancel -H "X-Rider-Id: $RIDER_A_ID"
   ```

   **Expected**: `fee_charged: 0, within_free_cutoff: true` when called more than 10 minutes
   before `ride_start_time`; `within_free_cutoff: false` and a nonzero `fee_charged` when called
   inside the 10-minute cutoff. Validates FR-008 and the clarified 10-minute cancellation cutoff.

5. **Verify contact-detail isolation**: grep every response captured above for either rider's
   raw phone number or email string — none should appear. This is the executable check for
   Constitution Principle I / SC-004.

## Success Criteria Mapping

| Spec Success Criterion | Validated by step |
|---|---|
| SC-001 (intent posted <60s) | Step 1 (manual timing during UI walkthrough) |
| SC-002 (50%+ match rate in-window) | Steps 1–2 |
| SC-003 (confirm/decline within 2 min) | Step 3 |
| SC-004 (zero contact-detail leaks) | Step 5 |
| SC-005 (no penalty fee before cutoff) | Step 4 |
