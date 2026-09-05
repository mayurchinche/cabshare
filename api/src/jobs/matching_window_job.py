"""Matching-window trigger job (FR-002a).

Runs on a short poll interval (APScheduler, ~15s per research.md) and, for every open intent
whose matching window has opened, attempts to pair it with another open, compatible intent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.src.models.match import Match, MatchStatus
from api.src.models.ride_intent import IntentStatus, RideIntent
from api.src.services.fare_service import compute_fare_split
from api.src.services.matching_service import Candidate, haversine_km, find_match
from api.src.services.notification_service import notify_match_proposed

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 15
CONFIRMATION_WINDOW_MINUTES = 10

# ponytail: flat per-km estimate stands in for a real fare-estimation API/partner quote; swap
# once a routing/fare-quote provider is chosen.
BASE_FARE_INR = 60.0
PER_KM_RATE_INR = 15.0


def _to_candidate(intent: RideIntent) -> Candidate:
    return Candidate(
        intent_id=str(intent.id),
        rider_id=str(intent.rider_id),
        rider_gender=intent.rider.gender,
        gender_preference=intent.gender_preference.value,
        destination_lat=intent.destination_lat,
        destination_lng=intent.destination_lng,
        matching_window_opens_at=intent.matching_window_opens_at,
        matching_window_closes_at=intent.matching_window_closes_at,
        created_at=intent.created_at,
    )


def run_matching_window_pass(db: Session, now: datetime | None = None) -> list[Match]:
    """Pair every eligible open intent once; returns the Match rows created this pass."""
    now = now or datetime.now(timezone.utc)

    open_intents = (
        db.execute(
            select(RideIntent).where(
                RideIntent.status == IntentStatus.OPEN,
                RideIntent.matching_window_opens_at <= now,
                RideIntent.matching_window_closes_at > now,
            )
        )
        .scalars()
        .all()
    )

    candidates = [_to_candidate(i) for i in open_intents]
    intents_by_id = {str(i.id): i for i in open_intents}
    already_matched_ids: set[str] = set()
    created_matches: list[Match] = []
    logger.debug("matching_window_pass.started candidate_count=%d", len(candidates))

    # FR-008/FR-009 rework: a mutually-declined pairing must never be re-offered to the same
    # two riders. Declines are recorded as `Match.status == CANCELLED`; derive the set of
    # already-declined rider pairs so the pool-building step below can exclude them.
    declined_matches = (
        db.execute(select(Match).where(Match.status == MatchStatus.CANCELLED)).scalars().all()
    )
    declined_rider_pairs: set[frozenset[str]] = {
        frozenset({str(m.intent_a.rider_id), str(m.intent_b.rider_id)}) for m in declined_matches
    }

    for subject in candidates:
        if subject.intent_id in already_matched_ids:
            continue
        pool = [
            c
            for c in candidates
            if c.intent_id != subject.intent_id
            and c.intent_id not in already_matched_ids
            and frozenset({subject.rider_id, c.rider_id}) not in declined_rider_pairs
        ]
        partner = find_match(subject, pool)
        if partner is None:
            continue

        subject_intent = intents_by_id[subject.intent_id]
        partner_intent = intents_by_id[partner.intent_id]

        distance_a = haversine_km(
            subject_intent.origin_lat,
            subject_intent.origin_lng,
            subject_intent.destination_lat,
            subject_intent.destination_lng,
        )
        distance_b = haversine_km(
            partner_intent.origin_lat,
            partner_intent.origin_lng,
            partner_intent.destination_lat,
            partner_intent.destination_lng,
        )
        total_fare = BASE_FARE_INR + PER_KM_RATE_INR * max(distance_a, distance_b)
        split = compute_fare_split(total_fare, distance_a, distance_b)

        match = Match(
            intent_a_id=subject_intent.id,
            intent_b_id=partner_intent.id,
            # The cab leg starts where the matched pair's trains land — the shared arrival
            # *station* — not at the origin station where they boarded. Each rider is then
            # dropped at their own real final destination (falls back to the station itself if
            # a rider skipped the drop-off picker, e.g. pre-existing intents).
            combined_stop_order=[
                {
                    "rider_role": "self",
                    "stop_type": "pickup",
                    "location": subject_intent.destination,
                    "latitude": subject_intent.destination_lat,
                    "longitude": subject_intent.destination_lng,
                },
                {
                    "rider_role": "partner",
                    "stop_type": "pickup",
                    "location": partner_intent.destination,
                    "latitude": partner_intent.destination_lat,
                    "longitude": partner_intent.destination_lng,
                },
                {
                    "rider_role": "self",
                    "stop_type": "drop",
                    "location": subject_intent.final_destination or subject_intent.destination,
                    "latitude": subject_intent.final_destination_lat
                    or subject_intent.destination_lat,
                    "longitude": subject_intent.final_destination_lng
                    or subject_intent.destination_lng,
                },
                {
                    "rider_role": "partner",
                    "stop_type": "drop",
                    "location": partner_intent.final_destination or partner_intent.destination,
                    "latitude": partner_intent.final_destination_lat
                    or partner_intent.destination_lat,
                    "longitude": partner_intent.final_destination_lng
                    or partner_intent.destination_lng,
                },
            ],
            fare_split={
                "total_fare": split.total_fare,
                "platform_fee_per_rider": split.platform_fee_per_rider,
                "rider_a_share": split.rider_a_share,
                "rider_b_share": split.rider_b_share,
            },
            status=MatchStatus.PROPOSED,
            confirmation_deadline=now.replace(microsecond=0)
            + timedelta(minutes=CONFIRMATION_WINDOW_MINUTES),
        )
        db.add(match)
        db.flush()  # populate match.id before assigning to intents

        subject_intent.status = IntentStatus.MATCHED
        subject_intent.match_id = match.id
        partner_intent.status = IntentStatus.MATCHED
        partner_intent.match_id = match.id

        already_matched_ids.add(subject.intent_id)
        already_matched_ids.add(partner.intent_id)
        created_matches.append(match)

    db.commit()
    logger.info("matching_window_pass.completed matches_created=%d", len(created_matches))
    for match in created_matches:
        notify_match_proposed(str(match.intent_a.rider_id), str(match.id))
        notify_match_proposed(str(match.intent_b.rider_id), str(match.id))
    return created_matches
