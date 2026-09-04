"""Contract smoke test for POST /rides/{id}/cancel (T041) — free before cutoff, fee after."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from api.src.models.match import Match, MatchStatus
from api.src.models.ride import Ride, RideStatus
from api.src.models.ride_intent import GenderPreference, IntentStatus, LuggageSize, RideIntent
from api.src.models.rider import Rider, VerificationStatus


def _make_confirmed_ride(db_session, cutoff_delta_minutes: int):
    db = db_session()
    now = datetime.now(timezone.utc)

    rider_a = Rider(
        phone_number="+911234500011", display_name="A", verification_status=VerificationStatus.VERIFIED
    )
    rider_b = Rider(
        phone_number="+911234500012", display_name="B", verification_status=VerificationStatus.VERIFIED
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
        combined_stop_order=[],
        fare_split={"total_fare": 200.0, "platform_fee_per_rider": 10.0, "rider_a_share": 100.0, "rider_b_share": 100.0},
        status=MatchStatus.CONFIRMED,
        confirmation_deadline=now + timedelta(minutes=10),
    )
    db.add(match)
    db.commit()

    ride = Ride(
        match_id=match.id,
        stop_order=[],
        fare_split=match.fare_split,
        status=RideStatus.READY,
        cancellation_cutoff_at=now + timedelta(minutes=cutoff_delta_minutes),
    )
    db.add(ride)
    db.commit()

    ride_id, rider_a_id = ride.id, rider_a.id
    db.close()
    return ride_id, rider_a_id


def test_cancel_before_cutoff_returns_no_fee(client, db_session):
    ride_id, rider_a_id = _make_confirmed_ride(db_session, cutoff_delta_minutes=10)

    resp = client.post(f"/rides/{ride_id}/cancel", headers={"X-Rider-Id": str(rider_a_id)})

    assert resp.status_code == 200
    body = resp.json()
    assert body["within_free_cutoff"] is True
    assert body["fee_charged"] == 0


def test_cancel_after_cutoff_returns_fee(client, db_session):
    ride_id, rider_a_id = _make_confirmed_ride(db_session, cutoff_delta_minutes=-1)

    resp = client.post(f"/rides/{ride_id}/cancel", headers={"X-Rider-Id": str(rider_a_id)})

    assert resp.status_code == 200
    body = resp.json()
    assert body["within_free_cutoff"] is False
    assert body["fee_charged"] > 0


def test_cancel_by_non_participant_returns_403(client, db_session):
    ride_id, _ = _make_confirmed_ride(db_session, cutoff_delta_minutes=10)

    resp = client.post(f"/rides/{ride_id}/cancel", headers={"X-Rider-Id": str(uuid.uuid4())})

    assert resp.status_code == 403
