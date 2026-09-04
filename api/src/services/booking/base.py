"""BookingProvider abstraction (Constitution Principle IV).

No cab-aggregator currently exposes a public multi-stop booking API for third parties, so the
MVP ships only `ManualConfirmationProvider`. Every future provider (an official partner API,
once one exists) implements this same interface and is selected via config — feature/matching
code must never call a partner API directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class StopOrderEntry:
    rider_id: str
    stop_type: str  # "pickup" | "drop"
    location: str


@dataclass
class FareSplit:
    total_fare: float
    platform_fee_per_rider: float
    rider_a_share: float
    rider_b_share: float


@dataclass
class BookedRide:
    """Provider-agnostic result of a booking attempt; persisted into the `Ride` model."""

    booking_provider: str
    status: str  # "ready" | "booked"
    provider_reference: str | None = None
    raw_provider_payload: dict[str, Any] | None = None


class BookingProvider(ABC):
    """Single interface every booking fulfillment path MUST go through."""

    @abstractmethod
    def book(self, stop_order: list[StopOrderEntry], fare_split: FareSplit) -> BookedRide:
        """Attempt to fulfill a ride booking for the given stop order and fare split."""
        raise NotImplementedError
