"""Matches API (T034): GET /matches/{id}, POST /matches/{id}/confirm, POST /matches/{id}/decline."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.src.api.deps import get_current_rider_id
from api.src.api.schemas.match import FareSplitOut, MatchOut, StopOut
from api.src.api.schemas.rider import MaskedRiderProfile
from api.src.db import get_db
from api.src.models.match import Match, MatchStatus
from api.src.models.ride_intent import IntentStatus
from api.src.models.rider import Rider
from api.src.services.matching_service import MatchConfirmationError, confirm_match, decline_match
from api.src.services.notification_service import notify_match_cancelled, notify_match_confirmed

router = APIRouter(prefix="/matches", tags=["matches"])


def _partner_intent(match: Match, rider_id: uuid.UUID):
    if match.intent_a.rider_id == rider_id:
        return match.intent_b
    if match.intent_b.rider_id == rider_id:
        return match.intent_a
    raise HTTPException(status_code=403, detail="Not a participant in this match")


def _to_match_out(match: Match, rider_id: uuid.UUID, db: Session) -> MatchOut:
    partner_intent = _partner_intent(match, rider_id)
    partner_rider = db.get(Rider, partner_intent.rider_id)

    is_rider_a = match.intent_a.rider_id == rider_id
    your_share = match.fare_split["rider_a_share"] if is_rider_a else match.fare_split["rider_b_share"]
    partner_share = match.fare_split["rider_b_share"] if is_rider_a else match.fare_split["rider_a_share"]

    return MatchOut(
        id=match.id,
        status=match.status,
        partner_profile=MaskedRiderProfile(
            display_name=partner_rider.display_name,
            photo_url=partner_rider.photo_url,
            rating=float(partner_rider.rating),
        ),
        combined_stop_order=[StopOut(**entry) for entry in match.combined_stop_order],
        fare_split=FareSplitOut(
            total_fare=match.fare_split["total_fare"],
            platform_fee_per_rider=match.fare_split["platform_fee_per_rider"],
            your_share=your_share,
            partner_share=partner_share,
        ),
        confirmation_deadline=match.confirmation_deadline,
    )


@router.get("/{match_id}", response_model=MatchOut)
def get_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> MatchOut:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return _to_match_out(match, rider_id, db)


@router.post("/{match_id}/confirm")
def confirm(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> dict:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        ride = confirm_match(match, str(rider_id), datetime.now(timezone.utc))
    except MatchConfirmationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if ride is not None:
        db.add(ride)
    db.commit()
    if ride is not None:
        notify_match_confirmed(str(match.intent_a.rider_id), str(ride.id))
        notify_match_confirmed(str(match.intent_b.rider_id), str(ride.id))
    return {"status": match.status.value, "ride_id": str(ride.id) if ride else None}


@router.post("/{match_id}/decline")
def decline(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    rider_id: uuid.UUID = Depends(get_current_rider_id),
) -> dict:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    _partner_intent(match, rider_id)  # 403 if rider isn't a participant

    if match.status != MatchStatus.PROPOSED:
        raise HTTPException(status_code=409, detail="Match is no longer pending confirmation")

    decline_match(match)
    # FR-008/FR-009: release both intents back to `open`, notified without attribution to the
    # declining rider.
    other_rider_id = (
        match.intent_b.rider_id if match.intent_a.rider_id == rider_id else match.intent_a.rider_id
    )
    match.intent_a.status = IntentStatus.OPEN
    match.intent_a.match_id = None
    match.intent_b.status = IntentStatus.OPEN
    match.intent_b.match_id = None
    db.commit()
    notify_match_cancelled(str(other_rider_id), str(match.id))
    return {"status": "cancelled"}
