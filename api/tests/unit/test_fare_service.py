"""Unit tests for fare_service (FR-006, FR-007)."""

from api.src.services.fare_service import compute_fare_split


def test_unequal_distances_produce_unequal_shares():
    result = compute_fare_split(
        total_fare=300.0, rider_a_stop_distance_km=1.0, rider_b_stop_distance_km=5.0
    )
    assert result.rider_a_share != result.rider_b_share
    assert result.rider_a_share < result.rider_b_share
    # Not a flat 50/50 split (clarified answer)
    assert result.rider_a_share != 150.0


def test_shares_sum_to_total_fare():
    result = compute_fare_split(
        total_fare=300.0, rider_a_stop_distance_km=2.0, rider_b_stop_distance_km=3.0
    )
    assert round(result.rider_a_share + result.rider_b_share, 2) == 300.0


def test_platform_fee_is_flat_ten_rupees_per_rider():
    result = compute_fare_split(
        total_fare=300.0, rider_a_stop_distance_km=2.0, rider_b_stop_distance_km=3.0
    )
    assert result.platform_fee_per_rider == 10.0


def test_zero_distance_falls_back_to_even_split():
    result = compute_fare_split(
        total_fare=100.0, rider_a_stop_distance_km=0.0, rider_b_stop_distance_km=0.0
    )
    assert result.rider_a_share == result.rider_b_share == 50.0
