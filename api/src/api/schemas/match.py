"""Pydantic schemas for the matches API (contracts/ride-pairing-api.yaml)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from api.src.api.schemas.rider import MaskedRiderProfile
from api.src.models.match import MatchStatus


class FareSplitOut(BaseModel):
    total_fare: float
    platform_fee_per_rider: float
    your_share: float
    partner_share: float


class StopOut(BaseModel):
    rider_role: str
    stop_type: str
    location: str
    latitude: float | None = None
    longitude: float | None = None


class MatchOut(BaseModel):
    """Never include `phone_number`/`email` — see MaskedRiderProfile (Constitution Principle I)."""

    id: uuid.UUID
    status: MatchStatus
    partner_profile: MaskedRiderProfile
    combined_stop_order: list[StopOut]
    fare_split: FareSplitOut
    confirmation_deadline: datetime

    model_config = {"from_attributes": True}
