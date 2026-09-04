"""Caching layer between the API endpoints and `TrainDataProvider` (Feature 003).

Two responsibilities:
1. `Train` reference rows are cached indefinitely (schedules change rarely) — search results are
   upserted so a train is only ever fetched from the provider once per `train_number`.
2. `TrainLiveStatusCache` rows are reused while "fresh" (`train_data_config.live_status_freshness_minutes`,
   default 15) to respect RailRadar's free-tier 1,000 req/month limit; a stale row is still
   returned (never deleted) if a fresh provider call fails, so the UI always has a "last known"
   status instead of an error.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.src.config import train_data_config
from api.src.models.train import Train, TrainLiveStatusCache
from api.src.services.train_data.base import LiveStatus, TrainDataProvider, TrainSearchResult
from api.src.services.train_data.railradar import RailRadarProvider


def get_provider() -> TrainDataProvider:
    return RailRadarProvider()


def search_trains(
    db: Session, provider: TrainDataProvider, from_code: str, to_code: str, travel_date: date | None
) -> list[TrainSearchResult]:
    results = provider.search_between(from_code, to_code, travel_date)
    for r in results:
        _upsert_train(db, r)
    db.commit()
    return results


def _upsert_train(db: Session, result: TrainSearchResult) -> Train:
    existing = db.execute(
        select(Train).where(Train.train_number == result.train_number)
    ).scalar_one_or_none()
    route_stub = [
        {
            "station_code": result.from_stop.station_code,
            "scheduled_arrival": result.from_stop.scheduled_arrival,
            "scheduled_departure": result.from_stop.scheduled_departure,
            "sequence": result.from_stop.sequence,
        },
        {
            "station_code": result.to_stop.station_code,
            "scheduled_arrival": result.to_stop.scheduled_arrival,
            "scheduled_departure": result.to_stop.scheduled_departure,
            "sequence": result.to_stop.sequence,
        },
    ]
    if existing:
        existing.train_name = result.train_name
        existing.route = route_stub
        existing.cached_at = datetime.now(timezone.utc)
        db.add(existing)
        return existing
    train = Train(
        train_number=result.train_number,
        train_name=result.train_name,
        route=route_stub,
        provider_source="railradar",
    )
    db.add(train)
    db.flush()
    return train


def get_live_status(
    db: Session, provider: TrainDataProvider, train_number: str, travel_date: date
) -> tuple[LiveStatus, bool]:
    """Returns (status, is_fresh). `is_fresh=False` means a stale cached row was returned because
    a fresh provider call was unavailable or the cache is still within its freshness window and
    was reused as-is (either way, the caller has *a* status to show)."""
    train = db.execute(
        select(Train).where(Train.train_number == train_number)
    ).scalar_one_or_none()

    cached: TrainLiveStatusCache | None = None
    if train:
        cached = db.execute(
            select(TrainLiveStatusCache)
            .where(
                TrainLiveStatusCache.train_id == train.id,
                TrainLiveStatusCache.travel_date == travel_date,
            )
            .order_by(TrainLiveStatusCache.fetched_at.desc())
        ).scalars().first()

    freshness_cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=train_data_config.live_status_freshness_minutes
    )
    if cached and cached.fetched_at >= freshness_cutoff:
        return _cache_row_to_status(cached, train_number, travel_date), True

    try:
        live = provider.get_live_status(train_number, travel_date)
    except Exception:
        if cached:
            return _cache_row_to_status(cached, train_number, travel_date), False
        raise

    if not train:
        train = Train(
            train_number=train_number, train_name=live.raw_payload.get("trainName", train_number)
        )
        db.add(train)
        db.flush()

    row = TrainLiveStatusCache(
        train_id=train.id,
        travel_date=travel_date,
        delay_minutes=live.delay_minutes,
        last_station_code=live.last_station_code,
        raw_payload=live.raw_payload,
        provider_source="railradar",
    )
    db.add(row)
    db.commit()
    return live, True


def _cache_row_to_status(
    row: TrainLiveStatusCache, train_number: str, travel_date: date
) -> LiveStatus:
    raw = row.raw_payload or {}
    current = raw.get("currentLocation") or {}
    next_halt = raw.get("nextHalt") or {}
    return LiveStatus(
        train_number=train_number,
        travel_date=travel_date,
        status=raw.get("status", "unknown"),
        delay_minutes=row.delay_minutes,
        last_station_code=row.last_station_code,
        last_station_name=current.get("stationName"),
        next_station_code=next_halt.get("stationCode"),
        next_station_name=next_halt.get("stationName"),
        segment_progress=current.get("segmentProgress"),
        raw_payload=raw,
    )
