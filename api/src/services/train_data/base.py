"""TrainDataProvider abstraction (mirrors `api/src/services/booking/base.py`'s pattern per
Constitution Principle IV): feature/matching code must never call a rail-data partner API
directly — always through this interface, so swapping/adding providers later is a config change,
not a rewrite.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class RouteStop:
    station_code: str
    station_name: str
    scheduled_arrival: str | None
    scheduled_departure: str | None
    sequence: int
    day: int = 0  # relative day-number of the train's own multi-day journey (RailRadar's `day`
    # field) — `to_stop.day - from_stop.day` gives how many calendar days after boarding the
    # rider's destination arrival falls on, independent of where the train itself originates.


@dataclass
class TrainSearchResult:
    train_number: str
    train_name: str
    from_stop: RouteStop
    to_stop: RouteStop
    distance_km: float | None = None
    duration_minutes: int | None = None


@dataclass
class LiveStatus:
    train_number: str
    travel_date: date
    status: str  # "running" | "scheduled" | "cancelled" | "unknown"
    delay_minutes: int | None
    last_station_code: str | None
    last_station_name: str | None
    next_station_code: str | None
    next_station_name: str | None
    segment_progress: float | None  # 0.0-1.0 between last/next station
    raw_payload: dict = field(default_factory=dict)


class TrainDataProvider(ABC):
    """Single interface every train-search/live-status path MUST go through."""

    @abstractmethod
    def search_between(
        self, from_station_code: str, to_station_code: str, travel_date: date | None = None
    ) -> list[TrainSearchResult]:
        raise NotImplementedError

    @abstractmethod
    def get_live_status(self, train_number: str, travel_date: date) -> LiveStatus:
        raise NotImplementedError
