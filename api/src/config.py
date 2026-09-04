"""Matching-parameter configuration.

Per Constitution Principle III, matching radius, window, and cancellation cutoff MUST be
externally configurable, never hardcoded in business logic. Values are sourced from environment
variables with the spec's defaults as fallbacks; swap `MatchingConfig.from_env()` for a DB-backed
per-city lookup later without touching callers.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchingConfig:
    radius_km: float = 2.0
    matching_window_minutes: int = 5
    cancellation_cutoff_minutes: int = 10
    platform_fee_inr: float = 10.0
    # ponytail: MVP has no real-time cab-arrival ETA (manual booking, no partner API); assume a
    # fixed buffer between "ready to book" and actual ride start so the cancellation cutoff has
    # something concrete to count down from. Revisit once a real ETA source exists.
    assumed_ride_start_buffer_minutes: int = 15
    # Feature 004: threshold (both riders' live ETA-to-common-station) below which the
    # auto_booking_prompt_job nudges riders to book their cab (Constitution Principle III —
    # configurable, not hardcoded).
    booking_prompt_eta_minutes: int = 8

    @classmethod
    def from_env(cls) -> "MatchingConfig":
        return cls(
            radius_km=float(os.getenv("CABSHARE_MATCH_RADIUS_KM", cls.radius_km)),
            matching_window_minutes=int(
                os.getenv("CABSHARE_MATCH_WINDOW_MIN", cls.matching_window_minutes)
            ),
            cancellation_cutoff_minutes=int(
                os.getenv("CABSHARE_CANCEL_CUTOFF_MIN", cls.cancellation_cutoff_minutes)
            ),
            platform_fee_inr=float(os.getenv("CABSHARE_PLATFORM_FEE_INR", cls.platform_fee_inr)),
            assumed_ride_start_buffer_minutes=int(
                os.getenv(
                    "CABSHARE_RIDE_START_BUFFER_MIN", cls.assumed_ride_start_buffer_minutes
                )
            ),
            booking_prompt_eta_minutes=int(
                os.getenv("CABSHARE_BOOKING_PROMPT_ETA_MIN", cls.booking_prompt_eta_minutes)
            ),
        )


matching_config = MatchingConfig.from_env()


@dataclass(frozen=True)
class TrainDataConfig:
    """Feature 003: live train data via RailRadar (https://railradar.in). Free-tier key is
    rate-limited to 1,000 requests/month — `TrainLiveStatusCache` freshness_minutes controls how
    aggressively we reuse a cached snapshot instead of re-calling the provider."""

    api_key: str | None = None
    base_url: str = "https://api.railradar.in/v1"
    live_status_freshness_minutes: int = 15

    @classmethod
    def from_env(cls) -> "TrainDataConfig":
        return cls(
            api_key=os.getenv("CABSHARE_RAILRADAR_API_KEY") or None,
            base_url=os.getenv("CABSHARE_RAILRADAR_BASE_URL", cls.base_url),
            live_status_freshness_minutes=int(
                os.getenv(
                    "CABSHARE_TRAIN_LIVE_FRESHNESS_MIN", cls.live_status_freshness_minutes
                )
            ),
        )


train_data_config = TrainDataConfig.from_env()
