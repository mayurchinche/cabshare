# Data Model: Station-to-Destination Ride Pairing (MVP)

Derived from `spec.md` Key Entities and Functional Requirements. Contact fields are intentionally
excluded from any entity/response that could be returned to a matched rider (Constitution
Principle I).

## Rider

Represents a verified app user.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `phone_number` | string, encrypted at rest | Never returned in match/ride API responses to another rider |
| `email` | string, encrypted at rest, nullable | Never returned in match/ride API responses to another rider |
| `display_name` | string | First name + last initial only (e.g., "Priya S.") — this is the only name form ever shown cross-rider |
| `photo_url` | string | Profile photo shown in masked profile |
| `rating` | decimal(3,2), default 5.00 | Rolling average from completed rides |
| `gender` | enum(`male`,`female`,`other`,`undisclosed`) | Used only for optional match filtering (FR-012) |
| `verification_status` | enum(`unverified`,`pending`,`verified`,`rejected`) | Gates intent posting/accepting (FR-011) |
| `created_at`, `updated_at` | timestamp | |

**Validation rules**: `verification_status` MUST be `verified` before a `RideIntent` can be
created for this rider. `phone_number` and `email` MUST NOT appear in any serializer used for
cross-rider responses (enforced by a dedicated `MaskedRiderProfile` schema — see contracts).

## RideIntent

A rider's request to share a ride.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `rider_id` | UUID (FK → Rider) | |
| `origin_station` | string + geo point | Station name and lat/long |
| `destination` | string + geo point | Free-text destination and geocoded lat/long |
| `luggage_size` | enum(`none`,`small`,`medium`,`large`) | Clarified Q2 |
| `expected_arrival_time` | timestamp | When the rider expects to reach `origin_station`; matching window opens at this time (FR-002a) |
| `gender_preference` | enum(`any`,`male`,`female`), nullable | Optional match filter (FR-012) |
| `status` | enum(`open`,`matched`,`expired`,`cancelled`) | |
| `matching_window_opens_at`, `matching_window_closes_at` | timestamp | Computed as `expected_arrival_time` + 5 minutes (FR-002a/b) |
| `created_at`, `updated_at` | timestamp | |

**State transitions**: `open` → `matched` (on successful pairing) · `open` → `expired`
(matching window closes with no match, FR-002b/FR-010) · `open`/`matched` → `cancelled`
(rider or partner cancels, FR-008/FR-009).

**Validation rules**: `destination` geo point MUST resolve within the configured matching radius
(default 2 km, Constitution Principle III) of another open intent's destination for a match to
be proposed. `expected_arrival_time` MUST be in the future at creation time.

## Match

A proposed or confirmed pairing of exactly two `RideIntent`s.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `intent_a_id`, `intent_b_id` | UUID (FK → RideIntent) | The two paired intents; `intent_a` is always the earlier-created (first-come-first-served, clarified Q5) |
| `combined_stop_order` | JSON array of `{rider_id, stop_type, location}` | Pickup/drop sequence for both riders |
| `fare_split` | JSON `{total_fare, platform_fee_per_rider, rider_a_share, rider_b_share}` | Distance-proportional (clarified Q4), itemized not opaque (FR-006) |
| `status` | enum(`proposed`,`confirmed`,`cancelled`,`expired`) | |
| `rider_a_confirmed_at`, `rider_b_confirmed_at` | timestamp, nullable | Both MUST be non-null before status can become `confirmed` (FR-005) |
| `confirmation_deadline` | timestamp | Match expires if not confirmed by both riders by this time |
| `created_at`, `updated_at` | timestamp | |

**Validation rules**: `status` MUST NOT become `confirmed` unless both `rider_a_confirmed_at`
and `rider_b_confirmed_at` are set (enforced in `matching_service`, not just at the API layer).
No field on `Match` or its API representation may include either rider's `phone_number` or
`email`.

## Ride

The bookable outcome of a confirmed `Match`.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `match_id` | UUID (FK → Match) | |
| `stop_order` | JSON array | Copied from `Match.combined_stop_order` at booking-ready time (FR-013) |
| `fare_split` | JSON | Copied from `Match.fare_split` at booking-ready time |
| `booking_provider` | enum(`manual_confirmation`) | Extensible: additional providers may be added later behind the same interface (Constitution Principle IV) |
| `status` | enum(`ready`,`booked`,`in_progress`,`completed`,`cancelled`) | |
| `cancellation_cutoff_at` | timestamp | `ride_start_time` − 10 minutes (clarified Q3); cancellations at/after this time may incur a fee |
| `created_at`, `updated_at` | timestamp | |

**Validation rules**: `status` transitions to `cancelled` (free) only if the cancelling action
occurs before `cancellation_cutoff_at`; otherwise a fee amount MUST be computed and shown before
the cancellation is finalized (FR-008).
