"""RideIntent model (FR-001, FR-002, FR-002a, FR-002b, FR-010, FR-012)."""

import enum
import uuid
from datetime import date as date_, datetime, timedelta, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.config import matching_config
from api.src.models.base import Base
from api.src.models.rider import Rider
from api.src.models.train import Train


class LuggageSize(str, enum.Enum):
    NONE = "none"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class GenderPreference(str, enum.Enum):
    ANY = "any"
    MALE = "male"
    FEMALE = "female"


class IntentStatus(str, enum.Enum):
    OPEN = "open"
    MATCHED = "matched"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RideIntent(Base):
    __tablename__ = "ride_intents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("riders.id"), index=True)
    rider: Mapped["Rider"] = relationship(lazy="joined")

    origin_station: Mapped[str] = mapped_column(String(200))
    # Geo point stored as WKT lat/long text at the model layer for portability; the matching
    # service casts these into a PostGIS geography for ST_DWithin radius queries.
    origin_lat: Mapped[float]
    origin_lng: Mapped[float]
    destination: Mapped[str] = mapped_column(String(200))
    destination_lat: Mapped[float]
    destination_lng: Mapped[float]

    luggage_size: Mapped[LuggageSize] = mapped_column(Enum(LuggageSize), default=LuggageSize.NONE)
    gender_preference: Mapped[GenderPreference] = mapped_column(
        Enum(GenderPreference), default=GenderPreference.ANY
    )

    expected_arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    matching_window_opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    matching_window_closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[IntentStatus] = mapped_column(Enum(IntentStatus), default=IntentStatus.OPEN)
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("matches.id", use_alter=True), nullable=True, default=None
    )

    # Feature 003 (data-model.md RideIntent extension): set when the rider picks a specific
    # train from route-search results. `travel_date` is required alongside it (validated in the
    # API layer) since the same train number runs on different calendar days.
    selected_train_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trains.id"), nullable=True, default=None
    )
    selected_train: Mapped["Train | None"] = relationship(lazy="joined", viewonly=True)
    travel_date: Mapped[date_ | None] = mapped_column(Date, nullable=True, default=None)

    @property
    def selected_train_number(self) -> str | None:
        return self.selected_train.train_number if self.selected_train else None

    # The rider's actual final drop-off (e.g. home/office) — distinct from `destination`, which
    # is the shared arrival *station* once a train is selected. The cab leg the matched pair
    # books runs from that shared station to each rider's own `final_destination` (two separate
    # drop stops on one shared cab), not to the station itself. Nullable/additive: riders who
    # skip train selection keep the old station-is-the-drop behaviour.
    final_destination: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    final_destination_lat: Mapped[float | None] = mapped_column(nullable=True, default=None)
    final_destination_lng: Mapped[float | None] = mapped_column(nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @staticmethod
    def compute_matching_window(expected_arrival_time: datetime) -> tuple[datetime, datetime]:
        """FR-002a: the 5-minute (config-driven) active-matching window starts at arrival time,
        not at intent-submission time."""
        opens_at = expected_arrival_time
        closes_at = expected_arrival_time + timedelta(
            minutes=matching_config.matching_window_minutes
        )
        return opens_at, closes_at
