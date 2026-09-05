"""ponytail: one-off station import from the free `datameet/railways` CC0 dataset (GitHub) —
run manually (`python -m api.scripts.seed_stations`) whenever a refresh is needed; not wired
into any live request path (see research.md's rationale: station data is effectively static).

Idempotent: upserts by `station_code` in batches via a single INSERT ... ON CONFLICT statement
per batch (not one row-at-a-time SELECT+INSERT) — a remote/free-tier Postgres over the public
internet has enough per-round-trip latency that ~9,000 individual row round trips reliably
times out mid-run with nothing committed; batching to ~1 round trip per 500 rows, with a
commit after each batch, makes this resilient to a mid-run drop (already-committed batches
just get skipped/no-op'd on re-run since they're upserts).
"""

from __future__ import annotations

import json
import urllib.request

from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.src.db import SessionLocal
from api.src.models.station import Station

DATASET_URL = "https://raw.githubusercontent.com/datameet/railways/master/stations.json"
DATASET_VERSION = "datameet-railways-v1"
BATCH_SIZE = 500


def _fetch_features() -> list[dict]:
    with urllib.request.urlopen(DATASET_URL, timeout=30) as resp:
        data = json.load(resp)
    return data["features"]


def _rows_from_features(features: list[dict]) -> list[dict]:
    rows = []
    for feature in features:
        props = feature.get("properties") or {}
        code = props.get("code")
        name = props.get("name")
        if not code or not name:
            continue  # skip malformed/placeholder rows (dataset has a few "XX-..." entries)

        geometry = feature.get("geometry")
        lat = lng = None
        if geometry and geometry.get("type") == "Point":
            lng, lat = geometry["coordinates"][0], geometry["coordinates"][1]

        rows.append(
            {
                "station_code": code,
                "name": name,
                "state": props.get("state"),
                "latitude": lat,
                "longitude": lng,
                "source_dataset_version": DATASET_VERSION,
            }
        )
    return rows


def main() -> None:
    rows = _rows_from_features(_fetch_features())
    db = SessionLocal()
    try:
        imported = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            stmt = pg_insert(Station).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Station.station_code],
                set_={
                    "name": stmt.excluded.name,
                    "state": stmt.excluded.state,
                    "latitude": stmt.excluded.latitude,
                    "longitude": stmt.excluded.longitude,
                    "source_dataset_version": stmt.excluded.source_dataset_version,
                },
            )
            db.execute(stmt)
            db.commit()  # commit per batch so a later network drop doesn't lose earlier batches
            imported += len(batch)
            print(f"  ...{imported}/{len(rows)}")
        print(f"Imported/refreshed {imported} stations from {DATASET_URL}")
    finally:
        db.close()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
