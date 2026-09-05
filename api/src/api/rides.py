"""Rides API (T041): POST /rides/{rideId}/cancel."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.src.api.deps import get_current_rider_id
from api.src.api.schemas.ride import CancellationResult, RideHistoryItem, RideStatusUpdateRequest
from api.src.db import get_db
from api.src.models.match import Match
from api.src.models.ride import Ride, RideStatus
from api.src.models.ride_intent import IntentStatus, RideIntent
from api.src.services.matching_service import cancel_ride
from api.src.services.notification_service import notify_match_cancelled

router = APIRouter(prefix="/rides", tags=["rides"])

# Item 6: manual status updates (no live GPS/driver-app integration yet, so riders self-report
# progress). Only forward transitions along the natural lifecycle — cancellation stays on the
# dedicated /cancel endpoint since only that path runs the free-cutoff/fee-charging logic.
_ALLOWED_STATUS_TRANSITIONS: dict[RideStatus, set[RideStatus]] = {
    RideStatus.READY: {RideStatus.BOOKED},
    RideStatus.BOOKED: {RideStatus.IN_PROGRESS},
    RideStatus.IN_PROGRESS: {RideStatus.COMPLETED},
    RideStatus.COMPLETED: set(),
    RideStatus.CANCELLED: set(),
}


@router.get("", response_model=list[RideHistoryItem])
def list_ride_history(
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> list[RideHistoryItem]:
    """RideHistoryList (Feature 004): every ride *request* this rider has ever made, newest
    first — including ones that never got a co-rider (still open, expired, cancelled), not
    just completed rides. Each such request is a "transaction" worth showing."""
    my_intents_query = db.query(RideIntent).filter(RideIntent.rider_id == rider_id)
    my_intents = my_intents_query.subquery()

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
    covered_match_ids: set[uuid.UUID] = set()
    for ride in rides:
        covered_match_ids.add(ride.match_id)
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

    # Any of this rider's own requests not already covered by a completed ride above — still
    # searching, expired unmatched, cancelled before a ride was booked, or matched but the ride
    # record hasn't been created yet. Shown with no partner/fare rather than being hidden.
    for intent in my_intents_query.order_by(RideIntent.created_at.desc()).all():
        if intent.match_id is not None and intent.match_id in covered_match_ids:
            continue
        partner_name = partner_rating = None
        if intent.match_id is not None:
            match = db.get(Match, intent.match_id)
            if match is not None:
                partner_intent = match.intent_b if match.intent_a_id == intent.id else match.intent_a
                partner_name = partner_intent.rider.display_name
                partner_rating = float(partner_intent.rider.rating)
        items.append(
            RideHistoryItem(
                id=str(intent.id),
                origin_station=intent.origin_station,
                destination=intent.destination,
                status=intent.status.value,
                partner_display_name=partner_name,
                partner_rating=partner_rating,
                created_at=intent.created_at.isoformat(),
            )
        )

    items.sort(key=lambda item: item.created_at, reverse=True)
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


@router.patch("/{ride_id}/status")
def update_status(
    ride_id: uuid.UUID,
    body: RideStatusUpdateRequest,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> dict:
    """Manual self-reported status update (item 6): either participant can advance a ride
    through its lifecycle since there's no live driver/GPS feed yet."""
    ride = db.get(Ride, ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    match = db.get(Match, ride.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found for ride")
    if rider_id not in (match.intent_a.rider_id, match.intent_b.rider_id):
        raise HTTPException(status_code=403, detail="Not a participant in this ride")

    try:
        new_status = RideStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid status value") from exc

    allowed = _ALLOWED_STATUS_TRANSITIONS.get(ride.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move ride from {ride.status.value} to {new_status.value}",
        )

    ride.status = new_status
    db.commit()
    return {"id": str(ride.id), "status": ride.status.value}
