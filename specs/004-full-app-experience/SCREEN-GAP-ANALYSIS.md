# Screen & Data Gap Analysis (Feature 004 + 003) — as of this validation pass

Purpose: answer "why don't I see all 16 screens" precisely — for each page, what's built,
what data it needs, and what's blocking it. Read alongside `PAGES.md` (page list) and
`DATABASE.md` (schema reference).

## Status per screen

| # | Page | File | Status | Data source | Blocker |
|---|------|------|--------|-------------|---------|
| 1 | Splash | `Splash.tsx` | ✅ built | none (local) | — |
| 2-3 | Phone Entry + OTP Verify | `Verification.tsx` (combined) | ✅ built | `riders.otp_request/confirm` | — |
| 4 | PAN/KYC Verify | `PanKyc.tsx` | ✅ built | `riders.kyc_submit` | — |
| 5 | Profile Setup | `ProfileSetup.tsx` | ✅ built | `riders.profile` | — |
| 6 | Home/Dashboard | `Home.tsx` | ✅ built | `riders/{id}/stats`, `/active-activity` | — |
| 7 | New Ride Request | `PostIntent.tsx` | ✅ built, uses free-text station strings (pre-003) | `intents.create` | — |
| 8 | Station & Train Picker | `StationPicker.tsx` ✅, `TrainPicker.tsx` ✅ | ✅ built | `Station` table (free dataset) + `GET /trains/search` (RailRadar, live) | — |
| 9 | Train Live Status | `TrainLiveStatus.tsx` | ✅ built | `GET /trains/{number}/live` (RailRadar, cached via `TrainLiveStatusCache`) | — |
| 10 | Searching/Matching | folded into `Home.tsx` "searching" active-activity state, not a distinct screen | ⚠️ partial | `active-activity` | build as its own screen (free, no blocker) |
| 11 | Match Found | `MatchReview.tsx` | ✅ built | `matches/{id}` | — |
| 12 | Ride Tracking (merge `RideConfirm` + live convergence) | `RideConfirm.tsx` (not yet merged) | ⚠️ partial | #9's live data now available — convergence rail still needs wiring | not blocked, just not implemented |
| 13 | Ride Cancel | `Cancel.tsx` | ✅ built | `rides/{id}/cancel` | — |
| 14 | Ride History List | `RideHistoryList.tsx` | ✅ built | `rides/history` | — |
| 15 | Ride History Detail | `RideHistoryDetail.tsx` | ✅ built | `rides/{id}` | — |
| 16 | Profile/Account | `ProfileAccount.tsx` | ✅ built | `riders/{id}/profile` | — |

**14 of 16 fully built and reachable. #9's live-train blocker is now resolved (user provided a
paid RailRadar API key — see below); #10 needs a one-screen split-out (no blocker); #12's
convergence rail is the only remaining real gap, now unblocked but not yet wired.**

## Former blocker, now resolved: live train data (#8, #9) via RailRadar

The user provided a paid RailRadar (`https://railradar.in`) API key (env var
`CABSHARE_RAILRADAR_API_KEY`). Implemented:
- `api/src/services/train_data/` — `TrainDataProvider` ABC (mirrors `services/booking/base.py`'s
  pattern) + `RailRadarProvider` implementation + `cache_service.py` (DB-backed cache respecting
  the free-tier 1,000 req/month limit via `Train`/`TrainLiveStatusCache` tables, 15-min freshness
  window, stale-but-available fallback if a live call fails).
- `GET /trains/search?from=&to=&date=` and `GET /trains/{number}/live?travel_date=` (`api/src/api/trains.py`).
- `RideIntent.selected_train_id`/`travel_date` (nullable, additive) — set when a rider picks a
  train from `TrainPicker.tsx` after choosing origin/destination stations in `PostIntent.tsx`.
- `TrainPicker.tsx` (route search results) and `TrainLiveStatus.tsx` (progress rail + delay chip,
  auto-refreshes every 60s, shows "last known status" if a live call fails) — both real, no mocks.

**Remaining work**: #12's convergence rail (wiring `TrainLiveStatus` data into `RideConfirm.tsx`'s
visual) and deciding whether `/stations/search` should also switch to RailRadar's
`/v1/lookup/search/stations` (potentially fresher than the static `datameet/railways` import) —
neither blocks any of the 16 screens from being reachable today.


## Test-data plan (so every scenario is exercisable without waiting on the RapidAPI decision)

`api/scripts/seed_demo_data.py` already seeds 2 KYC-verified riders with a `PROPOSED` match
(Pune Junction → Baner). Extend it (not yet done) to also seed, so every state is reachable
from Home without re-running the OTP flow each time:
- A **second pair** of riders with a match already `CONFIRMED` + a live `Ride` row → exercises
  #12 Ride Tracking / cancel-with-fee screens directly.
- A **third rider alone with no match** (`RideIntent` in `SEARCHING` status, no partner yet) →
  exercises the #10 Searching screen's empty/waiting state.
- **Ride history rows** (a `Ride` with `status=COMPLETED`) for one rider → exercises #14/#15
  with non-empty data (currently only the empty-state has been visually verified).

## Dev-only Screen Gallery (build this first — avoids the slow "navigate → screenshot" loop)

Add one `__DEV__`-gated route, `DevScreenGallery.tsx`, listing all 16 screens by name; tapping
one pushes it with realistic mock props (no login/API calls needed). Lets every screen be
visually reviewed against Figma in one sitting instead of walking the real 5+ tap user journey
each time. Stripped out of release builds automatically via the existing `__DEV__` guard
pattern (same one already used for the dev-OTP hint).
