"""ponytail: dev-only demo-data seeder — NOT wired into any production path, run manually
(`python -m api.scripts.seed_demo_data`) against a local/dev DB only. Creates two fully
onboarded (verified KYC + profile) demo riders with a matched Pune Junction -> Baner ride so
every downstream screen (MatchReview, RideConfirm, RideHistory, cancellation) can be exercised
without manually running two phone numbers through the OTP flow first.

Idempotent: re-running clears any previously-seeded demo rows (matched on the fixed demo phone
numbers below) before recreating them.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa

from api.src.db import SessionLocal
from api.src.models.kyc_document import DocumentType, KycDocument, KycStatus
from api.src.models.match import Match, MatchStatus
from api.src.models.ride import BookingProviderName, Ride, RideStatus
from api.src.models.ride_intent import GenderPreference, IntentStatus, LuggageSize, RideIntent
from api.src.models.rider import Gender, Rider, VerificationStatus
from api.src.services.encryption import encrypt

DEMO_PHONE_A = "+919000000001"
DEMO_PHONE_B = "+919000000002"

# Real-world coordinates for the two demo stops (Feature 003 station data will replace these
# with a proper lookup; hardcoded here since this is fixed seed/test data, not app logic).
PUNE_JN_LAT, PUNE_JN_LNG = 18.5286, 73.8745
BANER_LAT, BANER_LNG = 18.5599, 73.7869
# Each demo rider's own real final drop-off, distinct from the shared Baner *station* — this is
# what RideHistoryDetail/RideConfirm now show as each rider's individual cab drop stop.
RIDER_A_FINAL_DEST = "Baner Road IT Park, Baner, Pune"
RIDER_A_FINAL_LAT, RIDER_A_FINAL_LNG = 18.5594, 73.7899
RIDER_B_FINAL_DEST = "Aundh, Pune"
RIDER_B_FINAL_LAT, RIDER_B_FINAL_LNG = 18.5479, 73.8147



def _wipe_existing(db) -> None:
    existing = db.query(Rider).filter(Rider.phone_number.in_([DEMO_PHONE_A, DEMO_PHONE_B])).all()
    if not existing:
        return
    rider_ids = [r.id for r in existing]
    intents = db.query(RideIntent).filter(RideIntent.rider_id.in_(rider_ids)).all()
    intent_ids = [i.id for i in intents]
    # Query matches by FK directly (not just intent.match_id) so a match left dangling by a
    # prior interrupted run — e.g. one whose intent.match_id was already cleared/cancelled —
    # still gets swept up before we try to delete the intents it references.
    match_ids = {
        m.id
        for m in db.query(Match)
        .filter(sa.or_(Match.intent_a_id.in_(intent_ids), Match.intent_b_id.in_(intent_ids)))
        .all()
    }
    if match_ids:
        db.query(Ride).filter(Ride.match_id.in_(match_ids)).delete(synchronize_session=False)
        db.query(RideIntent).filter(RideIntent.id.in_(intent_ids)).update(
            {"match_id": None}, synchronize_session=False
        )
        db.query(Match).filter(Match.id.in_(match_ids)).delete(synchronize_session=False)
    db.query(RideIntent).filter(RideIntent.id.in_(intent_ids)).delete(synchronize_session=False)
    db.query(KycDocument).filter(KycDocument.rider_id.in_(rider_ids)).delete(synchronize_session=False)
    db.query(Rider).filter(Rider.id.in_(rider_ids)).delete(synchronize_session=False)
    db.commit()


def _make_rider(db, phone: str, name: str, gender: Gender) -> Rider:
    rider = Rider(
        id=uuid.uuid4(),
        phone_number=phone,
        display_name=name,
        gender=gender,
        rating=4.85,
        verification_status=VerificationStatus.VERIFIED,
    )
    db.add(rider)
    db.flush()
    db.add(
        KycDocument(
            rider_id=rider.id,
            document_type=DocumentType.PAN,
            pan_number_encrypted=encrypt("ABCDE1234F"),
            pan_number_last4="234F",
            pan_name_on_document=name.upper(),
            status=KycStatus.VERIFIED,
            verified_at=datetime.now(timezone.utc),
        )
    )
    return rider


def _make_intent(db, rider: Rider, arrival_offset_minutes: int) -> RideIntent:
    now = datetime.now(timezone.utc)
    arrival = now + timedelta(minutes=arrival_offset_minutes)
    opens_at, closes_at = RideIntent.compute_matching_window(arrival)
    final_dest, final_lat, final_lng = (
        (RIDER_A_FINAL_DEST, RIDER_A_FINAL_LAT, RIDER_A_FINAL_LNG)
        if rider.phone_number == DEMO_PHONE_A
        else (RIDER_B_FINAL_DEST, RIDER_B_FINAL_LAT, RIDER_B_FINAL_LNG)
    )
    intent = RideIntent(
        rider_id=rider.id,
        origin_station="Pune Junction",
        origin_lat=PUNE_JN_LAT,
        origin_lng=PUNE_JN_LNG,
        destination="Baner",
        destination_lat=BANER_LAT,
        destination_lng=BANER_LNG,
        luggage_size=LuggageSize.SMALL,
        gender_preference=GenderPreference.ANY,
        expected_arrival_time=arrival,
        matching_window_opens_at=opens_at,
        matching_window_closes_at=closes_at,
        status=IntentStatus.MATCHED,
        final_destination=final_dest,
        final_destination_lat=final_lat,
        final_destination_lng=final_lng,
    )
    db.add(intent)
    db.flush()
    return intent


def _make_completed_ride(db, rider_a: Rider, rider_b: Rider, days_ago: int, total_fare: float) -> Ride:
    """Seeds one past COMPLETED ride between the two demo riders so RideHistoryList/Detail have
    real content to validate, not just the single live active match."""
    past = datetime.now(timezone.utc) - timedelta(days=days_ago)
    arrival = past - timedelta(minutes=5)
    opens_at, closes_at = RideIntent.compute_matching_window(arrival)

    def _past_intent(rider: Rider) -> RideIntent:
        final_dest, final_lat, final_lng = (
            (RIDER_A_FINAL_DEST, RIDER_A_FINAL_LAT, RIDER_A_FINAL_LNG)
            if rider.phone_number == DEMO_PHONE_A
            else (RIDER_B_FINAL_DEST, RIDER_B_FINAL_LAT, RIDER_B_FINAL_LNG)
        )
        intent = RideIntent(
            rider_id=rider.id,
            origin_station="Pune Junction",
            origin_lat=PUNE_JN_LAT,
            origin_lng=PUNE_JN_LNG,
            destination="Baner",
            destination_lat=BANER_LAT,
            destination_lng=BANER_LNG,
            luggage_size=LuggageSize.SMALL,
            gender_preference=GenderPreference.ANY,
            expected_arrival_time=arrival,
            matching_window_opens_at=opens_at,
            matching_window_closes_at=closes_at,
            status=IntentStatus.MATCHED,
            final_destination=final_dest,
            final_destination_lat=final_lat,
            final_destination_lng=final_lng,
            created_at=past,
        )
        db.add(intent)
        db.flush()
        return intent

    intent_a = _past_intent(rider_a)
    intent_b = _past_intent(rider_b)

    fare_split = {
        "total_fare": total_fare,
        "platform_fee_per_rider": 10.0,
        "rider_a_share": round((total_fare - 20.0) / 2 + 10.0, 2),
        "rider_b_share": round((total_fare - 20.0) / 2 + 10.0, 2),
    }
    combined_stop_order = [
        {"rider_role": "self", "stop_type": "pickup", "location": "Baner", "latitude": BANER_LAT, "longitude": BANER_LNG},
        {"rider_role": "partner", "stop_type": "pickup", "location": "Baner", "latitude": BANER_LAT, "longitude": BANER_LNG},
        {"rider_role": "self", "stop_type": "drop", "location": RIDER_A_FINAL_DEST, "latitude": RIDER_A_FINAL_LAT, "longitude": RIDER_A_FINAL_LNG},
        {"rider_role": "partner", "stop_type": "drop", "location": RIDER_B_FINAL_DEST, "latitude": RIDER_B_FINAL_LAT, "longitude": RIDER_B_FINAL_LNG},
    ]

    match = Match(
        intent_a_id=intent_a.id,
        intent_b_id=intent_b.id,
        combined_stop_order=combined_stop_order,
        fare_split=fare_split,
        status=MatchStatus.CONFIRMED,
        confirmation_deadline=past + timedelta(minutes=10),
        rider_a_confirmed_at=past,
        rider_b_confirmed_at=past,
    )
    db.add(match)
    db.flush()
    intent_a.match_id = match.id
    intent_b.match_id = match.id

    ride = Ride(
        match_id=match.id,
        stop_order=combined_stop_order,
        fare_split=fare_split,
        booking_provider=BookingProviderName.MANUAL_CONFIRMATION,
        status=RideStatus.COMPLETED,
        cancellation_cutoff_at=past + timedelta(minutes=10),
        created_at=past,
    )
    db.add(ride)
    db.flush()
    return ride


def seed() -> None:
    db = SessionLocal()
    try:
        _wipe_existing(db)

        rider_a = _make_rider(db, DEMO_PHONE_A, "Aditi Sharma", Gender.FEMALE)
        rider_b = _make_rider(db, DEMO_PHONE_B, "Rohan Kulkarni", Gender.MALE)

        intent_a = _make_intent(db, rider_a, arrival_offset_minutes=20)
        intent_b = _make_intent(db, rider_b, arrival_offset_minutes=22)

        fare_split = {
            "total_fare": 240.0,
            "platform_fee_per_rider": 10.0,
            "rider_a_share": 130.0,
            "rider_b_share": 130.0,
        }
        combined_stop_order = [
            {"rider_role": "self", "stop_type": "pickup", "location": "Baner", "latitude": BANER_LAT, "longitude": BANER_LNG},
            {"rider_role": "partner", "stop_type": "pickup", "location": "Baner", "latitude": BANER_LAT, "longitude": BANER_LNG},
            {"rider_role": "self", "stop_type": "drop", "location": RIDER_A_FINAL_DEST, "latitude": RIDER_A_FINAL_LAT, "longitude": RIDER_A_FINAL_LNG},
            {"rider_role": "partner", "stop_type": "drop", "location": RIDER_B_FINAL_DEST, "latitude": RIDER_B_FINAL_LAT, "longitude": RIDER_B_FINAL_LNG},
        ]

        # Left as PROPOSED (not pre-confirmed) so logging in as either demo rider walks through
        # the *real* MatchReview -> confirm -> RideConfirm -> cancel flow via the actual API,
        # exercising the same code path a real match would use, rather than faking a Ride too.
        match = Match(
            intent_a_id=intent_a.id,
            intent_b_id=intent_b.id,
            combined_stop_order=combined_stop_order,
            fare_split=fare_split,
            status=MatchStatus.PROPOSED,
            # ponytail: generous window since this is seeded for manual/exploratory QA sessions
            # (not real matching, where the window is short by design) — bump if a session runs long.
            confirmation_deadline=datetime.now(timezone.utc) + timedelta(hours=6),
        )
        db.add(match)
        db.flush()

        intent_a.match_id = match.id
        intent_b.match_id = match.id
        db.commit()

        # Ride history content: two past COMPLETED rides so RideHistoryList/Detail have real
        # rows to show (not just today's live PROPOSED match above).
        ride_1 = _make_completed_ride(db, rider_a, rider_b, days_ago=5, total_fare=220.0)
        ride_2 = _make_completed_ride(db, rider_a, rider_b, days_ago=2, total_fare=260.0)
        db.commit()

        print("Seeded demo data:")
        print(f"  Rider A: {rider_a.display_name} ({DEMO_PHONE_A}) id={rider_a.id}")
        print(f"  Rider B: {rider_b.display_name} ({DEMO_PHONE_B}) id={rider_b.id}")
        print(f"  Match id={match.id} status={match.status.value} (PROPOSED, live/active)")
        print(f"  Completed ride history: {ride_1.id} (5 days ago), {ride_2.id} (2 days ago)")
        print("Log in as either demo phone number via the normal OTP flow (dev OTP is shown")
        print("on-screen in __DEV__ builds). Home will surface the pending match automatically")
        print("(GET /riders/{id}/active-activity) -> tap through to MatchReview to confirm,")
        print("then RideConfirm, then cancel -- exercising the real API end to end.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
