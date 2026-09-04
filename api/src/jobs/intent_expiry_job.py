"""Intent expiry job (FR-002a edge case).

Expires any OPEN intent whose matching window has closed without a match, so the rider
sees an "expired, please re-search" state instead of an intent stuck open forever.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api.src.models.ride_intent import IntentStatus, RideIntent

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30


def run_intent_expiry_pass(db: Session, now: datetime | None = None) -> int:
    """Marks expired intents; returns the number of intents expired."""
    now = now or datetime.now(timezone.utc)

    result = db.execute(
        update(RideIntent)
        .where(
            RideIntent.status == IntentStatus.OPEN,
            RideIntent.matching_window_closes_at <= now,
        )
        .values(status=IntentStatus.EXPIRED)
        .execution_options(synchronize_session=False)
    )
    db.commit()
    count = result.rowcount or 0
    if count:
        logger.info("intent_expiry_pass.completed expired_count=%d", count)
    return count
