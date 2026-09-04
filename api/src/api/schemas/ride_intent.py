"""Pydantic request/response schemas for the intents API (contracts/ride-pairing-api.yaml)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from api.src.models.ride_intent import GenderPreference, IntentStatus, LuggageSize


class RideIntentCreate(BaseModel):
    origin_station: str
    origin_lat: float
    origin_lng: float
    destination: str
    destination_lat: float
    destination_lng: float
    luggage_size: LuggageSize
    expected_arrival_time: datetime
    gender_preference: GenderPreference = GenderPreference.ANY
    # Feature 003 (data-model.md RideIntent extension): optional train pick from route search
    # (User Story 2). `train_number` (not an internal Train UUID — the client only ever sees
    # RailRadar's public train number) MUST come with `travel_date`.
    selected_train_number: str | None = None
    travel_date: date | None = None
    # The rider's exact drop-off point beyond the shared arrival station — see
    # models/ride_intent.py's `final_destination` docstring for why this is separate from
    # `destination`.
    final_destination: str | None = None
    final_destination_lat: float | None = None
    final_destination_lng: float | None = None

    @model_validator(mode="after")
    def _train_requires_travel_date(self) -> "RideIntentCreate":
        if self.selected_train_number and not self.travel_date:
            raise ValueError("travel_date is required when selected_train_number is set")
        return self


class RideIntentOut(BaseModel):
    id: uuid.UUID
    status: IntentStatus
    matching_window_opens_at: datetime
    matching_window_closes_at: datetime
    match_id: uuid.UUID | None = None
    selected_train_number: str | None = None
    travel_date: date | None = None
    final_destination: str | None = None
    final_destination_lat: float | None = None
    final_destination_lng: float | None = None

    model_config = {"from_attributes": True}

