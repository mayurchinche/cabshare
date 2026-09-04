"""Train search + live-status API (Feature 003): thin HTTP layer over
`services/train_data/cache_service.py`, which owns caching/rate-limit protection. Never calls
`RailRadarProvider` directly from here.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.src.api.schemas.train import LiveStatusOut, RouteStopOut, TrainSearchResultOut
from api.src.db import get_db
from api.src.services.train_data import cache_service
from api.src.services.train_data.railradar import RailRadarUnavailableError

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("/search", response_model=list[TrainSearchResultOut])
def search_trains(
    from_station: str = Query(..., alias="from", description="Origin station code, e.g. PUNE"),
    to_station: str = Query(..., alias="to", description="Destination station code, e.g. NDLS"),
    travel_date: date | None = Query(None),
    db: Session = Depends(get_db),
) -> list[TrainSearchResultOut]:
    provider = cache_service.get_provider()
    try:
        results = cache_service.search_trains(
            db, provider, from_station.upper(), to_station.upper(), travel_date
        )
    except RailRadarUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"Train data unavailable: {exc}") from exc

    return [
        TrainSearchResultOut(
            train_number=r.train_number,
            train_name=r.train_name,
            from_stop=RouteStopOut(**vars(r.from_stop)),
            to_stop=RouteStopOut(**vars(r.to_stop)),
            distance_km=r.distance_km,
            duration_minutes=r.duration_minutes,
        )
        for r in results
    ]


@router.get("/{train_number}/live", response_model=LiveStatusOut)
def live_status(
    train_number: str,
    travel_date: date = Query(..., description="Calendar date the train is running, YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> LiveStatusOut:
    provider = cache_service.get_provider()
    try:
        status, is_fresh = cache_service.get_live_status(db, provider, train_number, travel_date)
    except RailRadarUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"Live status unavailable: {exc}") from exc

    return LiveStatusOut(
        train_number=status.train_number,
        travel_date=status.travel_date,
        status=status.status,
        delay_minutes=status.delay_minutes,
        last_station_code=status.last_station_code,
        last_station_name=status.last_station_name,
        next_station_code=status.next_station_code,
        next_station_name=status.next_station_name,
        segment_progress=status.segment_progress,
        is_fresh=is_fresh,
    )
