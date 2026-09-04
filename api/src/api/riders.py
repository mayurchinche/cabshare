"""Signup/login API: phone OTP + PAN/KYC + profile (FR-011).

Onboarding order (Feature 004): phone OTP → PAN/KYC verification → profile setup. A rider's
`verification_status` is driven entirely by their `KycDocument` (see `kyc_service.py`) —
profile submission no longer auto-verifies (that was the old MVP placeholder; PAN verification
is the real gate now).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.src.api.schemas.rider import (
    ActiveActivityOut,
    KycStatusOut,
    KycSubmitIn,
    OtpConfirmIn,
    OtpConfirmOut,
    OtpRequestIn,
    OtpRequestOut,
    ProfileIn,
    RiderOut,
    RiderProfileOut,
    RiderStatsOut,
)
from api.src.db import get_db
from api.src.models.kyc_document import KycDocument
from api.src.models.match import Match
from api.src.models.ride import Ride, RideStatus
from api.src.models.ride_intent import IntentStatus, RideIntent
from api.src.models.rider import Rider
from api.src.services.kyc_service import submit_kyc
from api.src.services.verification_service import OtpService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/riders", tags=["riders"])

# ponytail: single process-wide in-memory OTP store (matches OtpService's own MVP scope) — fine
# for one API process; move to Redis/shared cache before running multiple instances.
_otp_service = OtpService()


def _normalize_phone(raw: str) -> str:
    """Canonicalize an India phone number so "9000000001", "919000000001", and
    "+919000000001" all resolve to the same rider record. Digits-only input of exactly
    10 digits is assumed to be a local India number and gets "+91" prepended; anything
    already carrying a country code (11+ digits or a leading "+") is normalized to "+<digits>".
    """
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 10:
        return f"+91{digits}"
    return f"+{digits}" if digits else raw


@router.post("/otp/request", response_model=OtpRequestOut, status_code=202)
def request_otp(payload: OtpRequestIn, db: Session = Depends(get_db)) -> OtpRequestOut:
    phone_number = _normalize_phone(payload.phone_number)
    rider = db.execute(select(Rider).where(Rider.phone_number == phone_number)).scalar_one_or_none()
    if rider is None:
        rider = Rider(id=uuid.uuid4(), phone_number=phone_number, display_name="")
        db.add(rider)
        db.commit()
        db.refresh(rider)

    code = _otp_service.request_otp(phone_number)
    logger.info("rider.otp_requested rider_id=%s", rider.id)
    return OtpRequestOut(rider_id=rider.id, debug_otp_code=code)


@router.post("/otp/confirm", response_model=OtpConfirmOut)
def confirm_otp(payload: OtpConfirmIn, db: Session = Depends(get_db)) -> OtpConfirmOut:
    phone_number = _normalize_phone(payload.phone_number)
    if not _otp_service.confirm_otp(phone_number, payload.code):
        raise HTTPException(status_code=401, detail="Incorrect or expired OTP code")

    rider = db.execute(select(Rider).where(Rider.phone_number == phone_number)).scalar_one_or_none()
    if rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")

    logger.info("rider.otp_confirmed rider_id=%s", rider.id)
    has_kyc = (
        db.execute(select(KycDocument.id).where(KycDocument.rider_id == rider.id)).first()
        is not None
    )
    return OtpConfirmOut(
        rider_id=rider.id,
        needs_kyc=not has_kyc,
        needs_profile=not rider.display_name,
    )


@router.post("/{rider_id}/kyc", response_model=KycStatusOut, status_code=201)
def submit_kyc_endpoint(rider_id: uuid.UUID, payload: KycSubmitIn, db: Session = Depends(get_db)) -> KycDocument:
    rider = db.get(Rider, rider_id)
    if rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")

    doc = submit_kyc(rider, payload.pan_number, payload.name_on_document)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{rider_id}/kyc", response_model=KycStatusOut)
def get_kyc_status(rider_id: uuid.UUID, db: Session = Depends(get_db)) -> KycDocument:
    doc = db.execute(
        select(KycDocument)
        .where(KycDocument.rider_id == rider_id)
        .order_by(KycDocument.created_at.desc())
    ).scalars().first()
    if doc is None:
        raise HTTPException(status_code=404, detail="No KYC submission found")
    return doc


@router.patch("/{rider_id}/profile", response_model=RiderOut)
def submit_profile(rider_id: uuid.UUID, payload: ProfileIn, db: Session = Depends(get_db)) -> Rider:
    rider = db.get(Rider, rider_id)
    if rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")

    rider.display_name = payload.display_name
    rider.gender = payload.gender
    rider.photo_url = payload.photo_url
    db.commit()
    db.refresh(rider)
    return rider


@router.get("/{rider_id}", response_model=RiderProfileOut)
def get_profile(rider_id: uuid.UUID, db: Session = Depends(get_db)) -> Rider:
    rider = db.get(Rider, rider_id)
    if rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")
    return rider


@router.get("/{rider_id}/stats", response_model=RiderStatsOut)
def get_stats(rider_id: uuid.UUID, db: Session = Depends(get_db)) -> RiderStatsOut:
    """Home dashboard (Feature 004, page 06): real ride count + lifetime savings, replacing the
    old `—` UI placeholders. Savings = sum of (what a solo cab would have cost) minus (what this
    rider actually paid), i.e. `total_fare - your_share` per completed ride — same fare-split
    fields already surfaced on the ride-history screen."""
    my_intent_ids = db.query(RideIntent.id).filter(RideIntent.rider_id == rider_id).subquery()

    rides = (
        db.query(Ride)
        .join(Match, Ride.match_id == Match.id)
        .filter(
            Ride.status == RideStatus.COMPLETED,
            (Match.intent_a_id.in_(db.query(my_intent_ids.c.id)))
            | (Match.intent_b_id.in_(db.query(my_intent_ids.c.id))),
        )
        .all()
    )

    total_saved = 0.0
    for ride in rides:
        match = db.get(Match, ride.match_id)
        is_a = match.intent_a.rider_id == rider_id
        fare = ride.fare_split or {}
        your_share = float(fare.get("rider_a_share" if is_a else "rider_b_share", 0.0))
        total_fare = float(fare.get("total_fare", 0.0))
        total_saved += max(total_fare - your_share, 0.0)

    return RiderStatsOut(rides_shared=len(rides), total_saved=round(total_saved, 2))


@router.get("/{rider_id}/active-activity", response_model=ActiveActivityOut)
def get_active_activity(rider_id: uuid.UUID, db: Session = Depends(get_db)) -> ActiveActivityOut:
    """Home dashboard: surfaces this rider's most recent non-terminal intent/match/ride so the
    app can resume the right screen (e.g. after a restart, or for pre-seeded demo data) instead
    of only being reachable via screen-to-screen navigation params."""
    intent = (
        db.query(RideIntent)
        .filter(
            RideIntent.rider_id == rider_id,
            RideIntent.status.in_([IntentStatus.OPEN, IntentStatus.MATCHED]),
        )
        .order_by(RideIntent.created_at.desc())
        .first()
    )
    if intent is None:
        return ActiveActivityOut()

    match = db.get(Match, intent.match_id) if intent.match_id else None
    ride = None
    if match is not None:
        ride = (
            db.query(Ride)
            .filter(Ride.match_id == match.id, Ride.status != RideStatus.CANCELLED)
            .order_by(Ride.created_at.desc())
            .first()
        )

    route_origin = route_destination = co_rider_name = None
    progress_percent = None
    if match is not None:
        is_a = match.intent_a.rider_id == rider_id
        my_intent = match.intent_a if is_a else match.intent_b
        partner_intent = match.intent_b if is_a else match.intent_a
        route_origin = my_intent.origin_station
        route_destination = my_intent.final_destination or my_intent.destination
        co_rider_name = partner_intent.rider.display_name or None
        if ride is not None:
            progress_percent = {
                RideStatus.READY: 10,
                RideStatus.BOOKED: 40,
                RideStatus.IN_PROGRESS: 70,
                RideStatus.COMPLETED: 100,
            }.get(ride.status, 10)

    return ActiveActivityOut(
        intent_id=intent.id,
        intent_status=intent.status.value,
        match_id=match.id if match else None,
        match_status=match.status.value if match else None,
        ride_id=ride.id if ride else None,
        ride_status=ride.status.value if ride else None,
        route_origin=route_origin,
        route_destination=route_destination,
        co_rider_name=co_rider_name,
        progress_percent=progress_percent,
    )
