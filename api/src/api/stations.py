"""Station search API (Feature 003, station-picker-only scope): free-text autocomplete over
the imported `stations` table (see `api/scripts/seed_stations.py`). Read-only, no writes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from api.src.api.schemas.station import StationOut
from api.src.db import get_db
from api.src.models.station import Station

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/search", response_model=list[StationOut])
def search_stations(
    q: str = Query(..., min_length=2, description="Station name or code prefix"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
) -> list[Station]:
    pattern = f"{q}%"
    stmt = (
        select(Station)
        .where(or_(Station.name.ilike(pattern), Station.station_code.ilike(pattern)))
        .order_by(Station.name)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())
