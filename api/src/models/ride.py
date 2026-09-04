"""Ride model (FR-008, FR-013) — the bookable outcome of a confirmed Match."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from api.src.models.base import Base


class BookingProviderName(str, enum.Enum):
    MANUAL_CONFIRMATION = "manual_confirmation"


class RideStatus(str, enum.Enum):
    READY = "ready"
    BOOKED = "booked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Ride(Base):
    __tablename__ = "rides"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"), unique=True, index=True)

    # Copied from Match.combined_stop_order / Match.fare_split at booking-ready time (FR-013) —
    # intentionally denormalized so a later Match edit can never retroactively alter a Ride.
    stop_order: Mapped[list] = mapped_column(JSON)
    fare_split: Mapped[dict] = mapped_column(JSON)

    booking_provider: Mapped[BookingProviderName] = mapped_column(
        Enum(BookingProviderName), default=BookingProviderName.MANUAL_CONFIRMATION
    )
    provider_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[RideStatus] = mapped_column(Enum(RideStatus), default=RideStatus.READY)

    cancellation_cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Feature 004: denormalized per-rider train number (like stop_order/fare_split above) so the
    # auto_booking_prompt_job can watch TrainLiveStatusCache without joining back through
    # RideIntent every poll. `booking_prompted_at` is set once, the first time both riders' live
    # ETA-to-common-station drops below `matching_config.booking_prompt_eta_minutes`.
    origin_train_number: Mapped[str | None] = mapped_column(String(10), nullable=True, default=None)
    booking_prompted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
