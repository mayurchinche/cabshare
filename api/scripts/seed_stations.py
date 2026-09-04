"""ponytail: one-off station import from the free `datameet/railways` CC0 dataset (GitHub) —
run manually (`python -m api.scripts.seed_stations`) whenever a refresh is needed; not wired
into any live request path (see research.md's rationale: station data is effectively static).

Idempotent: upserts by `station_code`, so re-running just refreshes rows instead of duplicating.
"""

from __future__ import annotations

import json
import urllib.request

import sqlalchemy as sa

from api.src.db import SessionLocal
from api.src.models.station import Station

DATASET_URL = "https://raw.githubusercontent.com/datameet/railways/master/stations.json"
DATASET_VERSION = "datameet-railways-v1"


def _fetch_features() -> list[dict]:
    with urllib.request.urlopen(DATASET_URL, timeout=30) as resp:
        data = json.load(resp)
    return data["features"]


def main() -> None:
    features = _fetch_features()
    db = SessionLocal()
    try:
        imported = 0
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

            existing = db.execute(
                sa.select(Station).where(Station.station_code == code)
            ).scalar_one_or_none()
            if existing:
                existing.name = name
                existing.state = props.get("state")
                existing.latitude = lat
                existing.longitude = lng
                existing.source_dataset_version = DATASET_VERSION
            else:
                db.add(
                    Station(
                        station_code=code,
                        name=name,
                        state=props.get("state"),
                        latitude=lat,
                        longitude=lng,
                        source_dataset_version=DATASET_VERSION,
                    )
                )
            imported += 1
        db.commit()
        print(f"Imported/refreshed {imported} stations from {DATASET_URL}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
