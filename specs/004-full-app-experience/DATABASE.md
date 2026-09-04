# CabShare — Database Schema Additions (Feature 004)

Base: existing Postgres+PostGIS schema (`riders`, `ride_intents`, `matches`, `rides`) +
Feature 003's `stations`, `trains`, `train_live_status_cache`. This document lists **only the
delta** needed for the full-app scope; nothing here duplicates data already covered by an
existing table.

## New table: `kyc_documents`

One row per verification attempt (keeps an audit trail instead of overwriting).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `rider_id` | UUID FK → riders.id | index |
| `document_type` | enum(`pan`) | only PAN in v1; enum leaves room for `aadhaar_last4` later without a migration rewrite |
| `pan_number_encrypted` | bytea | AES-256-GCM ciphertext (see Encryption below) — **never** plaintext, **never** in any API response |
| `pan_number_last4` | string(4) | plaintext, masked-display only (`XXXXX1234F`) — safe to return to the owning rider |
| `pan_name_on_document` | string(100) | for manual/automated name-match against `riders.display_name` |
| `status` | enum(`pending`,`verified`,`rejected`) | |
| `verified_at` | datetime, nullable | |
| `rejection_reason` | string(200), nullable | |
| `created_at` / `updated_at` | datetime | |

**Encryption**: application-layer AES-256-GCM using the `cryptography` package (already a
transitive dep of nothing new — it IS a new direct dependency, justified because there is no
stdlib AEAD cipher; this is the "only then: minimum code" rung, not a KMS integration).
Key sourced from `KYC_ENCRYPTION_KEY` env var (32-byte, base64) — `ponytail: env var key for
MVP; rotate to a managed KMS (AWS KMS/GCP KMS) before real PAN data hits production, this file
documents that as the explicit upgrade path`. Encrypt/decrypt logic lives in one new module,
`api/src/services/encryption.py`, imported only by the KYC service — never by matching/booking
code (keeps blast radius of "who touches PAN plaintext" to one file).

**Rider linkage**: `riders.verification_status` (already exists) becomes driven by
`kyc_documents.status` instead of the current auto-approve-on-profile-submit placeholder —
`VERIFIED` only once a `kyc_documents` row reaches `status = verified`.

No new columns on `riders` are needed — `verification_status` already exists and is repurposed.

## Reused as-is from Feature 003 (no changes)

- `stations` (code, name, lat/lng)
- `trains` (number, name, route stops + scheduled times)
- `train_live_status_cache` (train_number, date, current_station, delay_minutes, fetched_at)

## Extended table: `rides`

Two new columns to support the auto-booking-prompt flow (`RideTracking` page):

| Column | Type | Notes |
|---|---|---|
| `origin_train_number` | string(10), nullable | FK-by-value to `trains.number` for each rider's train (denormalized like `stop_order`/`fare_split` already are on this table) |
| `booking_prompted_at` | datetime, nullable | set once by `auto_booking_prompt_job` when both riders' live ETA-to-common-station drops below `matching_config.booking_prompt_eta_minutes` (new config value, mirrors the existing configurable-radius pattern — Constitution Principle III) |

## Ride history — no new table

`RideHistoryList`/`RideHistoryDetail` are **read-only queries**, not a new entity:
`SELECT rides.* JOIN matches JOIN ride_intents WHERE ride_intents.rider_id = :me ORDER BY
rides.created_at DESC`. Adding a denormalized "ride_history" table would violate the ladder
(rung 1 — doesn't need to exist) since the join is cheap at MVP scale and keeps a single
source of truth for ride status.

## Migration plan

One new Alembic migration: `add_kyc_documents_and_ride_booking_prompt.py`
- `CREATE TABLE kyc_documents ...`
- `ALTER TABLE rides ADD COLUMN origin_train_number ..., ADD COLUMN booking_prompted_at ...`

No changes to `matches`, `ride_intents`, `stations`, `trains`, `train_live_status_cache`.
