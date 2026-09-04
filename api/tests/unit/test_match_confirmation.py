"""Unit tests for confirm_match / decline_match / expire_unconfirmed_matches (T031, T032, T033)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.src.models.base import Base
from api.src.models.match import Match, MatchStatus
from api.src.models.ride import Ride
from api.src.models.ride_intent import GenderPreference, IntentStatus, LuggageSize, RideIntent
from api.src.models.rider import Rider, VerificationStatus
from api.src.services.matching_service import (
    MatchConfirmationError,
    confirm_match,
    decline_match,
    expire_unconfirmed_matches,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_matched_pair(db, now: datetime) -> tuple[RideIntent, RideIntent, Match]:
    rider_a = Rider(
        phone_number=f"+91{uuid.uuid4().int % 10**10:010d}",
        display_name="A",
        verification_status=VerificationStatus.VERIFIED,
    )
    rider_b = Rider(
        phone_number=f"+91{uuid.uuid4().int % 10**10:010d}",
        display_name="B",
        verification_status=VerificationStatus.VERIFIED,
    )
    db.add_all([rider_a, rider_b])
    db.commit()

    def make_intent(rider):
        return RideIntent(
            rider_id=rider.id,
            origin_station="Pune Jn",
            origin_lat=18.5286,
            origin_lng=73.8744,
            destination="Baner",
            destination_lat=18.5590,
            destination_lng=73.7868,
            luggage_size=LuggageSize.SMALL,
            gender_preference=GenderPreference.ANY,
            expected_arrival_time=now,
            matching_window_opens_at=now - timedelta(minutes=1),
            matching_window_closes_at=now + timedelta(minutes=4),
            status=IntentStatus.MATCHED,
        )

    intent_a = make_intent(rider_a)
    intent_b = make_intent(rider_b)
    db.add_all([intent_a, intent_b])
    db.commit()

    match = Match(
        intent_a_id=intent_a.id,
        intent_b_id=intent_b.id,
        combined_stop_order=[
            {"rider_role": "self", "stop_type": "pickup", "location": "Pune Jn"},
            {"rider_role": "self", "stop_type": "drop", "location": "Baner"},
        ],
        fare_split={
            "total_fare": 200.0,
            "platform_fee_per_rider": 10.0,
            "rider_a_share": 100.0,
            "rider_b_share": 100.0,
        },
        status=MatchStatus.PROPOSED,
        confirmation_deadline=now + timedelta(minutes=10),
    )
    db.add(match)
    db.commit()
    db.refresh(intent_a)
    db.refresh(intent_b)
    db.refresh(match)
    return intent_a, intent_b, match


def test_match_stays_proposed_after_only_one_rider_confirms(db):
    now = datetime.now(timezone.utc)
    intent_a, intent_b, match = _make_matched_pair(db, now)

    ride = confirm_match(match, str(intent_a.rider_id), now)

    assert ride is None
    assert match.status == MatchStatus.PROPOSED
    assert match.rider_a_confirmed_at is not None
    assert match.rider_b_confirmed_at is None


def test_match_confirms_and_creates_ride_once_both_confirm(db):
    now = datetime.now(timezone.utc)
    intent_a, intent_b, match = _make_matched_pair(db, now)

    first = confirm_match(match, str(intent_a.rider_id), now)
    second = confirm_match(match, str(intent_b.rider_id), now)

    assert first is None
    assert second is not None
    assert isinstance(second, Ride)
    assert match.status == MatchStatus.CONFIRMED
    assert second.status.value == "ready"
    assert second.fare_split == match.fare_split


def test_confirm_after_deadline_raises():
    now = datetime.now(timezone.utc)
    match = Match(
        intent_a_id=uuid.uuid4(),
        intent_b_id=uuid.uuid4(),
        combined_stop_order=[],
        fare_split={"total_fare": 0, "platform_fee_per_rider": 0, "rider_a_share": 0, "rider_b_share": 0},
        status=MatchStatus.PROPOSED,
        confirmation_deadline=now - timedelta(minutes=1),
    )

    with pytest.raises(MatchConfirmationError):
        confirm_match(match, "someone", now)


def test_decline_cancels_match(db):
    now = datetime.now(timezone.utc)
    _, _, match = _make_matched_pair(db, now)

    decline_match(match)

    assert match.status == MatchStatus.CANCELLED


def test_expire_unconfirmed_matches_past_deadline(db):
    now = datetime.now(timezone.utc)
    _, _, match = _make_matched_pair(db, now)
    match.confirmation_deadline = now - timedelta(seconds=1)

    expired = expire_unconfirmed_matches([match], now)

    assert expired == [match]
    assert match.status == MatchStatus.EXPIRED


def test_expire_unconfirmed_matches_skips_confirmed(db):
    now = datetime.now(timezone.utc)
    _, _, match = _make_matched_pair(db, now)
    match.status = MatchStatus.CONFIRMED
    match.confirmation_deadline = now - timedelta(seconds=1)

    expired = expire_unconfirmed_matches([match], now)

    assert expired == []
    assert match.status == MatchStatus.CONFIRMED
