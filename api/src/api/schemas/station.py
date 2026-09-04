"""Station schemas (Feature 003, station-picker-only scope)."""

import uuid

from pydantic import BaseModel


class StationOut(BaseModel):
    id: uuid.UUID
    station_code: str
    name: str
    state: str | None
    city: str | None
    latitude: float | None
    longitude: float | None
