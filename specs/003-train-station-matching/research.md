# Phase 0 Research: Train/Station-Based Ride Matching

## 1. Station master data source

**Decision**: Use `datameet/railways` (GitHub, CC0-licensed GeoJSON: station code, name, state,
zone, lat/lng, plus route-geometry and station-schedule files). Self-host by importing once into
the new `stations` table via a one-off seed job; do not call it live.

**Rationale**: No auth, no rate limit, no ToS ambiguity (CC0). Station codes/coordinates are
effectively static (last verified crowd-collected ~2016 but stations rarely close/move/rename),
so a periodic re-import is sufficient — no need for a live dependency for something this stable.

**Alternatives considered**:
- *data.gov.in Ministry of Railways datasets* — also free and official, requires registering for
  an `api-key`; kept as a secondary cross-check/refresh source, not primary, since the GitHub
  dataset is simpler to consume (flat GeoJSON, no key management) for a one-time import.
- *Calling a live "list stations" endpoint from an unofficial provider on every search* — rejected:
  adds a hard external dependency and rate-limit risk to a read that should be instant local
  autocomplete.

## 2. Train route search (station → station)

**Decision**: Build `TrainDataProvider` interface with two implementations shipped at once:
`static_fallback` (returns "no train data available, enter train number manually" — zero external
calls, ships first) and `rapidapi_irctc` (best-effort call to the RapidAPI "IRCTC1" unofficial
listing), selected via config. Cache every successful route-search response in the `trains` table
so repeated searches for the same station pair don't re-hit the provider.

**Rationale**: RapidAPI IRCTC1 is the most current/maintained unofficial option found (station
search, trains-between-stations, live status, PNR status in one listing); `indianrailapi.com` is
presently in maintenance and `railwayapi.com` appears defunct (redirects to confirmtkt.com), so
neither is safe to hard-depend on. Because none of these are officially sanctioned, the interface
boundary + config-gating + cache lets the app keep working (in schedule-only mode) if the provider
disappears entirely.

**Alternatives considered**:
- *indianrailapi.com* — rejected as primary (observed live in maintenance during research; free
  tier explicitly called out as the affected tier).
- *railwayapi.com* — rejected (redirects/404s, looks acquired/defunct).
- *Scraping NTES directly* — rejected: highest ToS/legal risk, most fragile, no material benefit
  over an existing unofficial wrapper.

## 3. Live running status

**Decision**: Treat as enhancement-only. `TrainDataProvider.get_live_status()` is called
best-effort with a short timeout, response cached in `train_live_status_cache` with an "as-of"
timestamp; UI always labels status "unavailable" or shows the as-of time rather than presenting
stale data as current. Matching's "similar arrival time" logic uses live status when fresh (e.g.
<15 min old), otherwise falls back to scheduled time automatically.

**Rationale**: Research confirms there is no dependable official free live-status API in India —
every option (RapidAPI IRCTC1, indianrailapi.com, railwayapi.com) is an unofficial NTES-scraping
layer with small free quotas and unstable uptime; consumer apps (Ixigo's "Where is my Train",
RailYatri, Trainman) don't publish public APIs at all. Building a hard dependency on any of these
would make the core matching feature unreliable. Scheduled-time fallback keeps the feature
functional regardless of upstream health.

**Alternatives considered**:
- *Treat live status as required for matching* — rejected: violates the plan's own Constraints
  (live status must never block ride-intent posting) and would make the whole feature as fragile
  as its weakest external dependency.
- *Build our own NTES scraper* — rejected: highest legal risk, most engineering effort, no better
  reliability than existing unofficial wrappers already provide.

## 4. Booking hand-off

**Decision**: "Book this train" opens an external deep link (IRCTC website/app or a third-party
ticketing deep link) pre-filled with train number, date, and station codes where the target
supports URL pre-fill; otherwise pre-fills an in-app summary screen with a "copy details" action.
No in-app payment or booking-transaction API is called.

**Rationale**: No free public Indian train-booking transaction API exists (IRCTC's official API
requires a commercial partnership agreement, which is out of scope/budget). This keeps the
feature honest with Constitution Principle IV (no unofficial booking API calls) while still
providing a useful hand-off.

**Alternatives considered**:
- *Integrate an unofficial "book a ticket" API* — rejected outright: unlike route/status data,
  a real money transaction through an unauthorized channel is a materially higher risk (financial,
  legal) that Principle IV explicitly forbids regardless of "no official alternative exists."

## 5. Matching extension (same train / similar arrival time)

**Decision**: Extend the existing `matching_service` (Feature 001) with two additional match-reason
strategies that run alongside the existing geo-radius strategy: (a) exact `train_number` + travel
`date` equality → "same train"; (b) same destination `station_id` + arrival-time delta within a
configurable window (default 30 min, using live status if fresh else schedule) → "similar arrival
time". Both reuse the existing masked-profile/mutual-confirm output shape, only adding a
`match_reason` + `timing_basis` field.

**Rationale**: Reuses proven infrastructure (Feature 001's matching service, config-driven window
per Constitution Principle III) instead of building a parallel matching system — smallest diff
that satisfies the new requirements.

**Alternatives considered**:
- *Separate standalone train-matching microservice* — rejected: unjustified complexity for an MVP;
  the existing matching service already has the config-driven-window and masked-profile patterns
  this feature needs.
