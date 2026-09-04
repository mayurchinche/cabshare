"""Contract test for intents endpoints (T027) — validates against
contracts/ride-pairing-api.yaml: POST /intents, GET /intents/{id}, POST /intents/{id}/research.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from api.src.models.match import Match  # noqa: F401  (registers table for create_all)
from api.src.models.ride_intent import RideIntent  # noqa: F401
from api.src.models.rider import Gender, Rider, VerificationStatus

def _make_verified_rider(db) -> Rider:
    rider = Rider(
        phone_number=f"+91{uuid.uuid4().int % 10**10:010d}",
        display_name="Priya S.",
        gender=Gender.FEMALE,
        verification_status=VerificationStatus.VERIFIED,
    )
    db.add(rider)
    db.commit()
    db.refresh(rider)
    return rider


def _intent_payload(**overrides) -> dict:
    payload = {
        "origin_station": "Pune Jn",
        "origin_lat": 18.5286,
        "origin_lng": 73.8744,
        "destination": "Baner",
        "destination_lat": 18.5590,
        "destination_lng": 73.7868,
        "luggage_size": "small",
        "expected_arrival_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "gender_preference": "any",
    }
    payload.update(overrides)
    return payload


def test_create_intent_returns_201_with_open_status(client, db_session):
    db = db_session()
    rider = _make_verified_rider(db)
    db.close()

    resp = client.post(
        "/intents", json=_intent_payload(), headers={"X-Rider-Id": str(rider.id)}
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "open"
    assert body["match_id"] is None
    assert "matching_window_opens_at" in body
    assert "matching_window_closes_at" in body


def test_create_intent_unverified_rider_returns_403(client, db_session):
    db = db_session()
    rider = Rider(
        phone_number=f"+91{uuid.uuid4().int % 10**10:010d}",
        display_name="Unverified U.",
        verification_status=VerificationStatus.UNVERIFIED,
    )
    db.add(rider)
    db.commit()
    db.refresh(rider)
    db.close()

    resp = client.post(
        "/intents", json=_intent_payload(), headers={"X-Rider-Id": str(rider.id)}
    )

    assert resp.status_code == 403


def test_get_intent_returns_current_status(client, db_session):
    db = db_session()
    rider = _make_verified_rider(db)
    db.close()

    created = client.post(
        "/intents", json=_intent_payload(), headers={"X-Rider-Id": str(rider.id)}
    ).json()

    resp = client.get(f"/intents/{created['id']}")

    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_intent_missing_returns_404(client, db_session):
    resp = client.get(f"/intents/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_research_on_open_intent_returns_409(client, db_session):
    db = db_session()
    rider = _make_verified_rider(db)
    db.close()

    created = client.post(
        "/intents", json=_intent_payload(), headers={"X-Rider-Id": str(rider.id)}
    ).json()

    resp = client.post(
        f"/intents/{created['id']}/research", headers={"X-Rider-Id": str(rider.id)}
    )

    assert resp.status_code == 409


def test_research_on_expired_intent_reopens_with_202(client, db_session):
    db = db_session()
    rider = _make_verified_rider(db)
    db.close()

    created = client.post(
        "/intents", json=_intent_payload(), headers={"X-Rider-Id": str(rider.id)}
    ).json()

    db = db_session()
    intent = db.get(RideIntent, uuid.UUID(created["id"]))
    from api.src.models.ride_intent import IntentStatus

    intent.status = IntentStatus.EXPIRED
    db.commit()
    db.close()

    resp = client.post(
        f"/intents/{created['id']}/research", headers={"X-Rider-Id": str(rider.id)}
    )

    assert resp.status_code == 202
    assert resp.json() == {"status": "research_started"}

    follow_up = client.get(f"/intents/{created['id']}").json()
    assert follow_up["status"] == "open"
