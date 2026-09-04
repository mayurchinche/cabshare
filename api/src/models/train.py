"""Train reference data + live-status cache (Feature 003 data-model.md, Train/TrainLiveStatusCache).

`Train` rows are populated lazily from `TrainDataProvider` route searches (never synthesized
client-side) and cached indefinitely — schedules change rarely. `TrainLiveStatusCache` is a
short-TTL cache of a single live-status snapshot, keyed by train + travel date, so the app never
calls the (rate-limited) provider on every screen render.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.src.models.base import Base


class Train(Base):
    __tablename__ = "trains"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    train_number: Mapped[str] = mapped_column(String, unique=True, index=True)
    train_name: Mapped[str] = mapped_column(String)
    # Ordered list of {station_code, scheduled_arrival, scheduled_departure, sequence}.
    route: Mapped[list] = mapped_column(JSON, default=list)
    provider_source: Mapped[str] = mapped_column(String, default="railradar")
    cached_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class TrainLiveStatusCache(Base):
    __tablename__ = "train_live_status_cache"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    train_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("trains.id"), index=True)
    travel_date: Mapped[date] = mapped_column(Date)
    delay_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_station_code: Mapped[str | None] = mapped_column(String, nullable=True)
    # Full provider response kept for richer UI (progress %, next-halt ETA, etc.) beyond the
    # spec's minimal columns — avoids a second round-trip for fields the UI needs.
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    provider_source: Mapped[str] = mapped_column(String, default="railradar")
