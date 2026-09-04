"""Train search/live-status schemas (Feature 003)."""

from datetime import date

from pydantic import BaseModel


class RouteStopOut(BaseModel):
    station_code: str
    station_name: str
    scheduled_arrival: str | None
    scheduled_departure: str | None
    sequence: int
    day: int


class TrainSearchResultOut(BaseModel):
    train_number: str
    train_name: str
    from_stop: RouteStopOut
    to_stop: RouteStopOut
    distance_km: float | None
    duration_minutes: int | None


class LiveStatusOut(BaseModel):
    train_number: str
    travel_date: date
    status: str
    delay_minutes: int | None
    last_station_code: str | None
    last_station_name: str | None
    next_station_code: str | None
    next_station_name: str | None
    segment_progress: float | None
    is_fresh: bool
