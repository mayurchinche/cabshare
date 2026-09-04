"""Fare-split calculation (FR-006, FR-007).

Distance-proportional per clarification: each rider pays a share of the base fare proportional
to their own stop's distance along the combined route (not a flat 50/50 split), plus a flat
platform fee per rider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from api.src.config import matching_config

logger = logging.getLogger(__name__)


@dataclass
class FareSplitResult:
    total_fare: float
    platform_fee_per_rider: float
    rider_a_share: float
    rider_b_share: float


def compute_fare_split(
    total_fare: float, rider_a_stop_distance_km: float, rider_b_stop_distance_km: float
) -> FareSplitResult:
    """Split `total_fare` proportionally to each rider's stop distance.

    Falls back to an even split only in the degenerate case where both distances are zero
    (e.g., identical drop points), to avoid a divide-by-zero.
    """
    total_distance = rider_a_stop_distance_km + rider_b_stop_distance_km
    if total_distance <= 0:
        rider_a_share = rider_b_share = total_fare / 2
    else:
        rider_a_share = total_fare * (rider_a_stop_distance_km / total_distance)
        rider_b_share = total_fare * (rider_b_stop_distance_km / total_distance)

    result = FareSplitResult(
        total_fare=total_fare,
        platform_fee_per_rider=matching_config.platform_fee_inr,
        rider_a_share=round(rider_a_share, 2),
        rider_b_share=round(rider_b_share, 2),
    )
    logger.debug(
        "fare.split_computed total_fare=%s rider_a_share=%s rider_b_share=%s",
        total_fare, result.rider_a_share, result.rider_b_share,
    )
    return result
