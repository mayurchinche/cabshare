"""MVP BookingProvider: no partner API call — the rider books via their own Ola/Uber/Rapido
app and confirms completion in-app. This provider only records that the ride is "ready" with
the finalized stop order/fare-split for the rider to act on.
"""

from api.src.services.booking.base import BookedRide, BookingProvider, FareSplit, StopOrderEntry


class ManualConfirmationProvider(BookingProvider):
    def book(self, stop_order: list[StopOrderEntry], fare_split: FareSplit) -> BookedRide:
        return BookedRide(
            booking_provider="manual_confirmation",
            status="ready",
            provider_reference=None,
            raw_provider_payload=None,
        )
