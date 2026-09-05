"""Pydantic schemas for the rides API (contracts/ride-pairing-api.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class CancellationResult(BaseModel):
    status: str = "cancelled"
    fee_charged: float
    within_free_cutoff: bool


class RideStatusUpdateRequest(BaseModel):
    """Item 6: manual self-reported ride status transition (booked/in_progress/completed)."""

    status: str


class RideHistoryItem(BaseModel):
    """RideHistoryList/RideHistoryDetail (Feature 004) — read-only projection over
    rides+matches+ride_intents, no new table (see DATABASE.md)."""

    id: str
    origin_station: str
    destination: str
    status: str
    # None for ride intents that never matched (still searching, expired, cancelled solo) —
    # every request is shown here even without a co-rider/fare yet.
    partner_display_name: str | None = None
    partner_rating: float | None = None
    your_share: float = 0.0
    total_fare: float = 0.0
    platform_fee: float = 0.0
    created_at: str
