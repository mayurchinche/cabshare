"""Match model (FR-005, FR-006, FR-013)."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.models.base import Base
from api.src.models.ride_intent import RideIntent  # noqa: F401  (registers mapper for the relationship below)


class MatchStatus(str, enum.Enum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    intent_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ride_intents.id"))
    intent_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ride_intents.id"))
    # viewonly: RideIntent.match_id is the "live" FK used for status queries; these relationships
    # are read-only navigational sugar so services can do `match.intent_a.rider_id` etc.
    intent_a: Mapped["RideIntent"] = relationship(
        foreign_keys=[intent_a_id], viewonly=True, lazy="joined"
    )
    intent_b: Mapped["RideIntent"] = relationship(
        foreign_keys=[intent_b_id], viewonly=True, lazy="joined"
    )

    # [{"rider_role": "self"|"partner", "stop_type": "pickup"|"drop", "location": str}, ...]
    combined_stop_order: Mapped[list] = mapped_column(JSON)
    # {"total_fare": float, "platform_fee_per_rider": float, "rider_a_share": float, "rider_b_share": float}
    fare_split: Mapped[dict] = mapped_column(JSON)

    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.PROPOSED)
    rider_a_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    rider_b_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    confirmation_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def both_confirmed(self) -> bool:
        return self.rider_a_confirmed_at is not None and self.rider_b_confirmed_at is not None
