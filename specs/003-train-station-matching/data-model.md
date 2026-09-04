# Data Model: Train/Station-Based Ride Matching

Extends Feature 001's `RideIntent`/`Match` entities and adds three new entities. Contact fields
remain excluded from any cross-rider response (Constitution Principle I, unchanged).

## Station (new)

Canonical railway station, seeded once from the `datameet/railways` dataset.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `station_code` | string, unique, indexed | e.g. `NDLS`; canonical identifier used everywhere else |
| `name` | string, indexed (trigram/prefix) | e.g. "New Delhi"; indexed for fast autocomplete |
| `state` | string | Used for disambiguating same-named stations (FR-012) |
| `city` | string, nullable | |
| `location` | geography(Point) | lat/lng, used for "nearby station" suggestions |
| `source_dataset_version` | string | Tracks which import this row came from, for future re-imports |

**Validation rules**: `station_code` is the only field ever used as a foreign key elsewhere — a
`name` alone is never sufficient to identify a station (FR-012).

## Train (new)

Reference data for a scheduled train service; populated lazily from `TrainDataProvider` route
searches and cached indefinitely (schedules change rarely).

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `train_number` | string, unique, indexed | e.g. "12951" |
| `train_name` | string | e.g. "Mumbai Rajdhani" |
| `route` | JSON array of `{station_code, scheduled_arrival, scheduled_departure, sequence}` | Ordered stops |
| `provider_source` | string | Which `TrainDataProvider` implementation supplied this (for cache-invalidation/debugging) |
| `cached_at` | timestamp | |

**Validation rules**: `route` MUST contain at least two stops. A train search result is only
persisted here after a successful provider response — never synthesized client-side.

## TrainLiveStatusCache (new)

Short-TTL cache of a single live-status snapshot for a specific train + travel date.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `train_id` | UUID (FK → Train) | |
| `travel_date` | date | Live status is date-specific (same train number runs daily) |
| `delay_minutes` | integer, nullable | `null` = unavailable, not "on time" |
| `last_station_code` | string, nullable | |
| `fetched_at` | timestamp | The "as-of" time shown to riders |
| `provider_source` | string | |

**Validation rules**: A row older than a configurable freshness threshold (default 15 minutes)
MUST be treated as stale by `matching_service` and by the UI (FR-005); stale rows are not deleted
(kept for "last known status" display) but MUST be visually/logically distinguished from fresh
ones.

## RideIntent (extended from Feature 001)

New/changed fields only — all Feature 001 fields and validation rules remain unchanged.

| Field | Type | Notes |
|---|---|---|
| `origin_station_id` | UUID (FK → Station), nullable | Replaces free-text `origin_station` when the rider uses the station picker (FR-001/FR-002) |
| `destination_station_id` | UUID (FK → Station), nullable | New — destination is now optionally a Station too, not just a free-text/geocoded point |
| `selected_train_id` | UUID (FK → Train), nullable | Set when the rider picks a specific train from the route search results (User Story 2) |
| `travel_date` | date, nullable | Required if `selected_train_id` is set — needed to key live status and "same train" matching |

**Validation rules**: If `selected_train_id` is set, `travel_date` MUST also be set. Existing
free-text `destination` field (Feature 001) remains valid for riders who skip the station picker —
station-based fields are additive, not a breaking replacement (per spec Assumptions).

## Match (extended from Feature 001)

New/changed fields only.

| Field | Type | Notes |
|---|---|---|
| `match_reason` | enum(`geo_radius`,`same_train`,`similar_arrival_time`) | `geo_radius` is Feature 001's existing default; the two new values are added by this feature (FR-007/FR-008) |
| `timing_basis` | enum(`live_status`,`scheduled`), nullable | Only set when `match_reason` involves train timing; records whether live or scheduled time was used, for auditability/debugging (FR-008) |
| `invalidated_at` | timestamp, nullable | Set when a previously-shown match is invalidated by cancellation or a timing-window break (FR-009); a non-null value means the match MUST be re-flagged/hidden in the UI |

**State transitions**: unchanged from Feature 001 (`proposed` → `confirmed` → `cancelled`), with
one addition: any state MAY transition to `invalidated_at` being set (independent of the main
status field) when the underlying `RideIntent` is cancelled or its timing basis breaks the match
window — this does not delete the match, it flags it (FR-009).
