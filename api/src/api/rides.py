"""Rides API (T041): POST /rides/{rideId}/cancel."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.src.api.deps import get_current_rider_id
from api.src.api.schemas.ride import CancellationResult, RideHistoryItem
from api.src.db import get_db
from api.src.models.match import Match
from api.src.models.ride import Ride
from api.src.models.ride_intent import IntentStatus, RideIntent
from api.src.services.matching_service import cancel_ride
from api.src.services.notification_service import notify_match_cancelled

router = APIRouter(prefix="/rides", tags=["rides"])


@router.get("", response_model=list[RideHistoryItem])
def list_ride_history(
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> list[RideHistoryItem]:
    """RideHistoryList (Feature 004): every ride this rider has been part of, newest first."""
    my_intents = db.query(RideIntent.id, RideIntent.rider_id).filter(
        RideIntent.rider_id == rider_id
    ).subquery()

    rides = (
        db.query(Ride)
        .join(Match, Ride.match_id == Match.id)
        .filter(
            (Match.intent_a_id.in_(db.query(my_intents.c.id)))
            | (Match.intent_b_id.in_(db.query(my_intents.c.id)))
        )
        .order_by(Ride.created_at.desc())
        .all()
    )

    items: list[RideHistoryItem] = []
    for ride in rides:
        match = db.get(Match, ride.match_id)
        is_a = match.intent_a.rider_id == rider_id
        mine, partner = (match.intent_a, match.intent_b) if is_a else (match.intent_b, match.intent_a)
        fare = ride.fare_split or {}
        items.append(
            RideHistoryItem(
                id=str(ride.id),
                origin_station=mine.origin_station,
                destination=mine.destination,
                status=ride.status.value,
                partner_display_name=partner.rider.display_name,
                partner_rating=float(partner.rider.rating),
                your_share=float(fare.get("rider_a_share" if is_a else "rider_b_share", 0.0)),
                total_fare=float(fare.get("total_fare", 0.0)),
                platform_fee=float(fare.get("platform_fee_per_rider", 0.0)),
                created_at=ride.created_at.isoformat(),
            )
        )
    return items


@router.post("/{ride_id}/cancel", response_model=CancellationResult)
def cancel(
    ride_id: uuid.UUID,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> CancellationResult:
    ride = db.get(Ride, ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    match = db.get(Match, ride.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found for ride")

    if match.intent_a.rider_id == rider_id:
        other_rider_id = match.intent_b.rider_id
    elif match.intent_b.rider_id == rider_id:
        other_rider_id = match.intent_a.rider_id
    else:
        raise HTTPException(status_code=403, detail="Not a participant in this ride")

    outcome = cancel_ride(ride, match, datetime.now(timezone.utc))

    # FR-008/US3: the ride is cancelled outright for the MVP (no re-pairing a third rider mid-
    # flight); each rider's own intent is released back to `open` so they can rebook solo or
    # re-enter matching independently.
    match.intent_a.status = IntentStatus.OPEN
    match.intent_a.match_id = None
    match.intent_b.status = IntentStatus.OPEN
    match.intent_b.match_id = None

    db.commit()

    notify_match_cancelled(str(other_rider_id), str(match.id))

    return CancellationResult(
        fee_charged=outcome.fee_charged, within_free_cutoff=outcome.within_free_cutoff
    )
