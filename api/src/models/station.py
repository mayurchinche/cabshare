"""Station model (Feature 003, station-picker-only scope).

Canonical railway station reference data, imported once from the free `datameet/railways`
CC0 dataset (see `api/scripts/seed_stations.py`). Read-only from the app's perspective — never
written to by any rider-facing endpoint.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from api.src.models.base import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    station_code: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    source_dataset_version: Mapped[str] = mapped_column(String, default="datameet-railways-v1")

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
