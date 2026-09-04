"""Push notification dispatch (T036) for match-proposed / match-confirmed / match-cancelled
events.

ponytail: no FCM/APNs project exists yet for this MVP, so `LoggingNotificationSender` is the
only implementation — it just logs what *would* be sent. Real push wiring plugs in behind the
same `NotificationSender` interface later (mirrors the `BookingProvider` abstraction pattern),
so callers (`matching_service`, the matches/intents routers) never change.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("cabshare.notifications")


class NotificationSender(ABC):
    @abstractmethod
    def send(self, rider_id: str, title: str, body: str, data: dict[str, str]) -> None:
        raise NotImplementedError


class LoggingNotificationSender(NotificationSender):
    """MVP stub: logs the notification instead of calling a real FCM/APNs provider."""

    def send(self, rider_id: str, title: str, body: str, data: dict[str, str]) -> None:
        logger.info("push_notification rider_id=%s title=%r body=%r data=%s", rider_id, title, body, data)


_sender: NotificationSender = LoggingNotificationSender()


def notify_match_proposed(rider_id: str, match_id: str) -> None:
    """FR-005: both riders in a newly-proposed match must be told to review it."""
    _sender.send(
        rider_id,
        title="Ride share found!",
        body="Review and confirm your shared ride before the window closes.",
        data={"type": "match_proposed", "match_id": match_id},
    )


def notify_match_confirmed(rider_id: str, ride_id: str) -> None:
    """Both riders confirmed — the ride is ready to book."""
    _sender.send(
        rider_id,
        title="Ride confirmed",
        body="Your shared ride is ready — open the app to book your cab.",
        data={"type": "match_confirmed", "ride_id": ride_id},
    )


def notify_match_cancelled(rider_id: str, match_id: str) -> None:
    """FR-008/FR-009: notify the OTHER rider without attributing which rider cancelled."""
    _sender.send(
        rider_id,
        title="Ride share cancelled",
        body="Your shared ride was cancelled. You can search again anytime.",
        data={"type": "match_cancelled", "match_id": match_id},
    )
