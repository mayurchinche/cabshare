"""Contract test (T035): Match/MaskedRiderProfile API responses must never leak
`phone_number`/`email` — Constitution Principle I."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from api.src.models.match import Match, MatchStatus
from api.src.models.ride_intent import GenderPreference, IntentStatus, LuggageSize, RideIntent
from api.src.models.rider import Rider, VerificationStatus

def _make_proposed_match(db_session):
    db = db_session()
    now = datetime.now(timezone.utc)

    rider_a = Rider(
        phone_number="+911234500001",
        email="rider.a@example.com",
        display_name="Priya S.",
        verification_status=VerificationStatus.VERIFIED,
    )
    rider_b = Rider(
        phone_number="+911234500002",
        email="rider.b@example.com",
        display_name="Rahul K.",
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
    db.refresh(match)
    db.refresh(rider_a)
    match_id, rider_a_id, rider_a_phone, rider_a_email = (
        match.id,
        rider_a.id,
        rider_a.phone_number,
        rider_a.email,
    )
    db.close()
    return match_id, rider_a_id, rider_a_phone, rider_a_email


def test_get_match_response_never_contains_contact_fields(client, db_session):
    match_id, rider_a_id, rider_a_phone, rider_a_email = _make_proposed_match(db_session)

    resp = client.get(f"/matches/{match_id}", headers={"X-Rider-Id": str(rider_a_id)})

    assert resp.status_code == 200
    raw_body = resp.text
    body = resp.json()

    # Field-name check: the schema must not even declare these fields.
    assert "phone_number" not in body["partner_profile"]
    assert "email" not in body["partner_profile"]

    # Value-leak check: neither rider's actual contact values may appear anywhere in the payload,
    # even under an unexpected key.
    assert rider_a_phone not in raw_body
    assert rider_a_email not in raw_body

    # Only the masked fields are present.
    assert set(body["partner_profile"].keys()) == {"display_name", "photo_url", "rating"}
