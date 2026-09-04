"""Unit tests for matching_service.

Covers: first-come-first-served tie-break (clarified Q5), radius boundary enforcement,
matching-window overlap enforcement, and gender-preference filtering (FR-012) — closing the
analyze-phase gaps E1 (gender filter untested/unenforced) and C1 (only tie-break was tested).
"""

from datetime import datetime, timedelta, timezone

from api.src.models.rider import Gender
from api.src.services.matching_service import Candidate, find_match

NOW = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
PUNE_JN = (18.5286, 73.8744)  # lat, lng
BANER = (18.5590, 73.7868)  # ~9km from Pune Jn as the crow flies... use closer points below
BANER_NEAR = (18.5300, 73.8750)  # within ~2km of PUNE_JN for radius tests


def make_candidate(
    intent_id: str,
    created_at: datetime,
    lat: float = BANER_NEAR[0],
    lng: float = BANER_NEAR[1],
    window_opens: datetime = NOW,
    window_closes: datetime | None = None,
    gender: Gender = Gender.UNDISCLOSED,
    gender_preference: str = "any",
) -> Candidate:
    return Candidate(
        intent_id=intent_id,
        rider_id=f"rider-{intent_id}",
        rider_gender=gender,
        gender_preference=gender_preference,
        destination_lat=lat,
        destination_lng=lng,
        matching_window_opens_at=window_opens,
        matching_window_closes_at=window_closes or (window_opens + timedelta(minutes=5)),
        created_at=created_at,
    )


def test_earliest_two_paired_first_when_three_plus_compatible():
    subject = make_candidate("A", created_at=NOW)
    earliest = make_candidate("B", created_at=NOW + timedelta(seconds=1))
    later = make_candidate("C", created_at=NOW + timedelta(seconds=30))

    result = find_match(subject, [earliest, later])

    assert result is not None
    assert result.intent_id == "B"


def test_destinations_beyond_radius_are_not_matched():
    subject = make_candidate("A", created_at=NOW, lat=PUNE_JN[0], lng=PUNE_JN[1])
    far_away = make_candidate("B", created_at=NOW, lat=BANER[0], lng=BANER[1])  # ~9km away

    result = find_match(subject, [far_away])

    assert result is None


def test_non_overlapping_matching_windows_are_not_matched():
    subject = make_candidate("A", created_at=NOW, window_opens=NOW)
    non_overlapping = make_candidate(
        "B", created_at=NOW, window_opens=NOW + timedelta(minutes=10)
    )

    result = find_match(subject, [non_overlapping])

    assert result is None


def test_overlapping_matching_windows_are_matched():
    subject = make_candidate("A", created_at=NOW, window_opens=NOW)
    overlapping = make_candidate("B", created_at=NOW, window_opens=NOW + timedelta(minutes=2))

    result = find_match(subject, [overlapping])

    assert result is not None
    assert result.intent_id == "B"


def test_gender_preference_excludes_incompatible_candidate():
    subject = make_candidate(
        "A", created_at=NOW, gender=Gender.FEMALE, gender_preference="female"
    )
    incompatible = make_candidate("B", created_at=NOW, gender=Gender.MALE)

    result = find_match(subject, [incompatible])

    assert result is None


def test_gender_preference_allows_compatible_candidate():
    subject = make_candidate(
        "A", created_at=NOW, gender=Gender.FEMALE, gender_preference="female"
    )
    compatible = make_candidate("B", created_at=NOW, gender=Gender.FEMALE)

    result = find_match(subject, [compatible])

    assert result is not None
    assert result.intent_id == "B"
