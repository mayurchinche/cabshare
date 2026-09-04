# Research: Station-to-Destination Ride Pairing (MVP)

All Technical Context items were resolved during planning (no `NEEDS CLARIFICATION` markers).
This document records the decision, rationale, and alternatives considered for each notable
choice.

## 1. Matching-window trigger mechanism

- **Decision**: A scheduled worker (APScheduler) polls every 15s for intents whose expected
  arrival time has been reached and opens a 5-minute active-matching window for them; a second
  job expires intents whose window has elapsed with no match.
- **Rationale**: Matches the clarified requirement that active matching starts at expected
  arrival time, not at submission time. Polling every 15s keeps decision latency well under the
  5-minute window while staying simple to implement/operate for an MVP's traffic volume.
- **Alternatives considered**: Event-driven matching via a message queue (Kafka/SQS) — rejected
  for MVP as unnecessary operational overhead at pilot scale (~5k concurrent intents); can be
  swapped in later behind the same matching-service interface if throughput demands it.

## 2. Geo-radius matching

- **Decision**: PostgreSQL + PostGIS, using `ST_DWithin` on destination lat/long points with the
  radius read from config (default 2 km per Constitution Principle III).
- **Rationale**: PostGIS is the standard, battle-tested geo extension for Postgres; `ST_DWithin`
  is index-friendly (GiST) and avoids hand-rolled haversine math.
- **Alternatives considered**: Application-level haversine distance calculation — rejected as
  slower at scale and not index-backed.

## 3. Real-time match/cancel notification

- **Decision**: Push notifications (FCM for Android, APNs for iOS) trigger on match-proposed,
  match-confirmed, and cancellation events; the app also polls a lightweight status endpoint as
  a fallback if push delivery fails.
- **Rationale**: Push gives near-instant updates without battery-draining constant polling;
  the polling fallback keeps the flow working if push is delayed or blocked.
- **Alternatives considered**: WebSocket/long-lived connection — rejected as added
  infrastructure complexity not justified for MVP notification volume.

## 4. Fare-split calculation

- **Decision**: Distance-proportional split, computed from each rider's stop distance along the
  combined route (via a mapping/directions provider) as a proportion of total route distance;
  displayed as an itemized breakdown (base fare share + platform fee) before confirmation.
- **Rationale**: Matches the clarified requirement (Q: equal vs. proportional split → distance-
  proportional) and keeps the calculation auditable/testable independent of which cab partner
  ultimately fulfills the ride.
- **Alternatives considered**: Flat 50/50 split — rejected per clarification as unfair when stop
  distances differ meaningfully.

## 5. Booking fulfillment abstraction

- **Decision**: A single `BookingProvider` interface with one MVP implementation,
  `ManualConfirmationProvider`: the app shows the rider the finalized stop order and fare
  breakdown, the rider books via their own Ola/Uber/Rapido app, and confirms completion in-app.
- **Rationale**: No aggregator currently exposes a public multi-stop booking API for third
  parties (per Constitution Principle IV); building automation against an API that doesn't exist
  would be pure waste. The interface boundary means a real partner API integration can be added
  later without touching matching/fare logic.
- **Alternatives considered**: Scraping/unofficial partner API calls — explicitly disallowed by
  the constitution (compliance and reliability risk).

## 6. Identity verification

- **Decision**: Phone OTP (via SMS provider) plus a one-time photo/ID check (manual or
  third-party ID-verification API) gates a rider's ability to post or accept any intent;
  verification status is stored once and reused across all future intents.
- **Rationale**: Matches Constitution Principle II (Safety-First Matching) and the spec
  assumption that verification is a one-time onboarding step.
- **Alternatives considered**: Phone OTP only (no ID check) — rejected as insufficient trust
  signal for pairing strangers for a physical ride together.
