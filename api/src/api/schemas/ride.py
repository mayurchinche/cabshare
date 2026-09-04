"""Pydantic schemas for the rides API (contracts/ride-pairing-api.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class CancellationResult(BaseModel):
    status: str = "cancelled"
    fee_charged: float
    within_free_cutoff: bool


class RideHistoryItem(BaseModel):
    """RideHistoryList/RideHistoryDetail (Feature 004) — read-only projection over
    rides+matches+ride_intents, no new table (see DATABASE.md)."""

    id: str
    origin_station: str
    destination: str
    status: str
    partner_display_name: str
    partner_rating: float
    your_share: float
    total_fare: float
    platform_fee: float
    created_at: str
