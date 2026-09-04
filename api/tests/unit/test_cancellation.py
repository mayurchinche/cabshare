"""Unit tests for cancel_ride (T039, T040): free before cutoff, fee at/after cutoff."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from api.src.config import matching_config
from api.src.models.match import Match, MatchStatus
from api.src.models.ride import Ride, RideStatus
from api.src.services.matching_service import cancel_ride


def _make_ride_and_match(cutoff: datetime) -> tuple[Ride, Match]:
    match = Match(
        intent_a_id=uuid.uuid4(),
        intent_b_id=uuid.uuid4(),
        combined_stop_order=[],
        fare_split={"total_fare": 0, "platform_fee_per_rider": 0, "rider_a_share": 0, "rider_b_share": 0},
        status=MatchStatus.CONFIRMED,
        confirmation_deadline=cutoff,
    )
    ride = Ride(
        match_id=uuid.uuid4(),
        stop_order=[],
        fare_split={},
        status=RideStatus.READY,
        cancellation_cutoff_at=cutoff,
    )
    return ride, match


def test_cancel_before_cutoff_is_free():
    now = datetime.now(timezone.utc)
    ride, match = _make_ride_and_match(cutoff=now + timedelta(minutes=10))

    outcome = cancel_ride(ride, match, now)

    assert outcome.within_free_cutoff is True
    assert outcome.fee_charged == 0
    assert ride.status == RideStatus.CANCELLED
    assert match.status == MatchStatus.CANCELLED


def test_cancel_at_or_after_cutoff_charges_fee():
    now = datetime.now(timezone.utc)
    ride, match = _make_ride_and_match(cutoff=now - timedelta(seconds=1))

    outcome = cancel_ride(ride, match, now)

    assert outcome.within_free_cutoff is False
    assert outcome.fee_charged == matching_config.platform_fee_inr
    assert outcome.fee_charged > 0
