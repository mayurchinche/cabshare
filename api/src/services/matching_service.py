"""Matching service (FR-002, FR-002a, FR-012; Constitution Principles II & III).

Pure-Python candidate filtering/tie-break logic, kept independent of the DB layer so it's
directly unit-testable. In production this runs against a PostGIS `ST_DWithin` pre-filtered
candidate set (the radius check below is redundant-but-cheap insurance, not the primary index).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from api.src.config import matching_config
from api.src.models.match import Match, MatchStatus
from api.src.models.ride import BookingProviderName, Ride, RideStatus
from api.src.models.rider import Gender
from api.src.services.booking.base import FareSplit, StopOrderEntry
from api.src.services.booking.manual_confirmation import ManualConfirmationProvider

# Structured logging: only ever log opaque IDs (intent/match/ride/rider) and status enums —
# never phone_number/email/full names (Constitution Principle I).
logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


class MatchConfirmationError(Exception):
    """Raised when a confirm/decline action is invalid for a match's current state."""


def _as_aware_utc(dt: datetime) -> datetime:
    """SQLite (used in tests) silently drops tzinfo on round-trip; Postgres (production)
    preserves it. Normalize to UTC-aware so comparisons never raise regardless of backend."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)



@dataclass
class Candidate:
    intent_id: str
    rider_id: str
    rider_gender: Gender
    gender_preference: str  # "any" | "male" | "female"
    destination_lat: float
    destination_lng: float
    matching_window_opens_at: datetime
    matching_window_closes_at: datetime
    created_at: datetime


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _within_radius(a: Candidate, b: Candidate) -> bool:
    return (
        haversine_km(a.destination_lat, a.destination_lng, b.destination_lat, b.destination_lng)
        <= matching_config.radius_km
    )


def _windows_overlap(a: Candidate, b: Candidate) -> bool:
    return a.matching_window_opens_at < b.matching_window_closes_at and (
        b.matching_window_opens_at < a.matching_window_closes_at
    )


def _gender_compatible(a: Candidate, b: Candidate) -> bool:
    """FR-012: each rider's gender_preference (if set to something other than 'any') must be
    satisfied by the other rider's actual gender."""
    a_ok = a.gender_preference == "any" or a.gender_preference == b.rider_gender.value
    b_ok = b.gender_preference == "any" or b.gender_preference == a.rider_gender.value
    return a_ok and b_ok


def find_match(subject: Candidate, pool: list[Candidate]) -> Candidate | None:
    """Return the best compatible candidate for `subject` from `pool`, or None.

    Tie-break (clarified): strictly first-come-first-served by intent creation time — no
    best-fit scoring in MVP.
    """
    compatible = [
        c
        for c in pool
        if c.intent_id != subject.intent_id
        and _within_radius(subject, c)
        and _windows_overlap(subject, c)
        and _gender_compatible(subject, c)
    ]
    if not compatible:
        logger.info("match.none_found intent_id=%s pool_size=%d", subject.intent_id, len(pool))
        return None
    best = min(compatible, key=lambda c: c.created_at)
    logger.info(
        "match.found intent_id=%s partner_intent_id=%s candidates=%d",
        subject.intent_id, best.intent_id, len(compatible),
    )
    return best


def confirm_match(match: Match, rider_id: str, now: datetime) -> Ride | None:
    """FR-005: record one rider's confirmation; only create the `Ride` once BOTH riders have
    confirmed. Returns the newly-created `Ride`, or None if still waiting on the other rider.

    Raises `MatchConfirmationError` if the confirmation deadline has already passed (409 at the
    API layer) — callers must not silently accept a late confirmation.
    """
    if now >= _as_aware_utc(match.confirmation_deadline):
        logger.warning("match.confirm_late_rejected match_id=%s rider_id=%s", match.id, rider_id)
        raise MatchConfirmationError("Confirmation deadline has passed")
    if match.status != MatchStatus.PROPOSED:
        raise MatchConfirmationError(f"Match is not awaiting confirmation (status={match.status})")

    intent_a_rider_id = str(match.intent_a.rider_id)
    intent_b_rider_id = str(match.intent_b.rider_id)
    if rider_id == intent_a_rider_id:
        match.rider_a_confirmed_at = now
    elif rider_id == intent_b_rider_id:
        match.rider_b_confirmed_at = now
    else:
        raise MatchConfirmationError("Rider is not a participant in this match")

    logger.info("match.confirmed_by_rider match_id=%s rider_id=%s", match.id, rider_id)

    if not match.both_confirmed:
        return None

    match.status = MatchStatus.CONFIRMED
    provider = ManualConfirmationProvider()
    stop_order = [
        StopOrderEntry(
            rider_id=entry.get("rider_role", ""), stop_type=entry["stop_type"], location=entry["location"]
        )
        for entry in match.combined_stop_order
    ]
    fare_split = FareSplit(**match.fare_split)
    booked = provider.book(stop_order, fare_split)

    cutoff_minutes = matching_config.cancellation_cutoff_minutes
    buffer_minutes = matching_config.assumed_ride_start_buffer_minutes
    cancellation_cutoff_at = now + timedelta(minutes=buffer_minutes - cutoff_minutes)

    ride = Ride(
        match_id=match.id,
        stop_order=match.combined_stop_order,
        fare_split=match.fare_split,
        booking_provider=BookingProviderName(booked.booking_provider),
        provider_reference=booked.provider_reference,
        status=RideStatus.READY if booked.status == "ready" else RideStatus.BOOKED,
        cancellation_cutoff_at=cancellation_cutoff_at,
    )
    logger.info(
        "ride.created match_id=%s ride_status=%s provider=%s",
        match.id, ride.status, ride.booking_provider,
    )
    return ride


def decline_match(match: Match) -> None:
    """FR-008/FR-009: either rider declining cancels the whole match; both intents return to
    `open` so each can be re-matched (handled by the caller, which owns the RideIntent rows)."""
    match.status = MatchStatus.CANCELLED
    logger.info("match.declined match_id=%s", match.id)


def expire_unconfirmed_matches(matches: list[Match], now: datetime) -> list[Match]:
    """T033: any `proposed` match whose confirmation_deadline has passed without both
    confirmations is cancelled so its intents can be released back to `open` by the caller."""
    expired = []
    for match in matches:
        if match.status == MatchStatus.PROPOSED and now >= _as_aware_utc(match.confirmation_deadline):
            match.status = MatchStatus.EXPIRED
            expired.append(match)
    if expired:
        logger.info("match.expired count=%d match_ids=%s", len(expired), [m.id for m in expired])
    return expired


@dataclass
class CancellationOutcome:
    within_free_cutoff: bool
    fee_charged: float


def cancel_ride(ride: Ride, match: Match, now: datetime) -> CancellationOutcome:
    """FR-008: free cancellation before `cancellation_cutoff_at`; a fee applies at/after it.

    ponytail: the spec only defines one concrete monetary figure (the ₹10 platform fee), so the
    late-cancellation penalty reuses `matching_config.platform_fee_inr` rather than inventing an
    unspecified percentage-of-fare charge. Revisit once product defines a real penalty schedule.
    """
    within_free_cutoff = now < _as_aware_utc(ride.cancellation_cutoff_at)
    fee_charged = 0.0 if within_free_cutoff else matching_config.platform_fee_inr

    ride.status = RideStatus.CANCELLED
    match.status = MatchStatus.CANCELLED

    logger.info(
        "ride.cancelled ride_id=%s match_id=%s within_free_cutoff=%s fee_charged=%s",
        ride.id, match.id, within_free_cutoff, fee_charged,
    )

    return CancellationOutcome(within_free_cutoff=within_free_cutoff, fee_charged=fee_charged)
