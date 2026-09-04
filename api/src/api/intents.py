"""Intents API (T025, T026): POST /intents, GET /intents/{id}, POST /intents/{id}/research."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.src.api.deps import get_current_rider_id
from api.src.api.schemas.ride_intent import RideIntentCreate, RideIntentOut
from api.src.config import matching_config
from api.src.db import get_db
from api.src.models.ride_intent import IntentStatus, RideIntent
from api.src.models.rider import Rider
from api.src.models.train import Train
from api.src.services.verification_service import VerificationError, require_verified

router = APIRouter(prefix="/intents", tags=["intents"])


@router.post("", response_model=RideIntentOut, status_code=201)
def create_ride_intent(
    payload: RideIntentCreate,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> RideIntent:
    rider = db.get(Rider, rider_id)
    if rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")
    try:
        require_verified(rider)
    except VerificationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    opens_at, closes_at = RideIntent.compute_matching_window(payload.expected_arrival_time)
    selected_train_id = None
    if payload.selected_train_number:
        train = db.execute(
            select(Train).where(Train.train_number == payload.selected_train_number)
        ).scalar_one_or_none()
        if train is None:
            raise HTTPException(status_code=404, detail="Selected train not found — search again")
        selected_train_id = train.id
    intent = RideIntent(
        rider_id=rider_id,
        origin_station=payload.origin_station,
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        destination=payload.destination,
        destination_lat=payload.destination_lat,
        destination_lng=payload.destination_lng,
        luggage_size=payload.luggage_size,
        gender_preference=payload.gender_preference,
        expected_arrival_time=payload.expected_arrival_time,
        matching_window_opens_at=opens_at,
        matching_window_closes_at=closes_at,
        status=IntentStatus.OPEN,
        selected_train_id=selected_train_id,
        travel_date=payload.travel_date,
        final_destination=payload.final_destination,
        final_destination_lat=payload.final_destination_lat,
        final_destination_lng=payload.final_destination_lng,
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)
    return intent


@router.get("/{intent_id}", response_model=RideIntentOut)
def get_ride_intent(intent_id: uuid.UUID, db: Session = Depends(get_db)) -> RideIntent:
    intent = db.get(RideIntent, intent_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Intent not found")
    return intent


@router.post("/{intent_id}/research", status_code=202)
def research_ride_intent(
    intent_id: uuid.UUID,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> dict:
    """FR-002b manual re-search: only valid for an intent that already expired with no match."""
    intent = db.get(RideIntent, intent_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Intent not found")
    if intent.rider_id != rider_id:
        raise HTTPException(status_code=403, detail="Not your intent")
    if intent.status != IntentStatus.EXPIRED:
        raise HTTPException(
            status_code=409, detail="Only an expired intent can be re-searched"
        )

    # Re-search opens a fresh window starting now (not the original expected_arrival_time,
    # which has already passed) — FR-002b.
    now = datetime.now(timezone.utc)
    intent.status = IntentStatus.OPEN
    intent.matching_window_opens_at = now
    intent.matching_window_closes_at = now + timedelta(
        minutes=matching_config.matching_window_minutes
    )
    db.commit()
    return {"status": "research_started"}
