"""Rider model.

Contact fields (`phone_number`, `email`) live here but MUST NEVER be included in any
schema/serializer that can be returned about a rider to their matched partner
(Constitution Principle I). See `api/src/api/schemas/rider.py::MaskedRiderProfile`.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from api.src.models.base import Base


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed"


class Rider(Base):
    __tablename__ = "riders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Contact fields: encrypted at rest (handled at the DB/column-type layer in production;
    # left as plain String here since the encryption backend is an infra concern, not a model
    # concern). NEVER expose these via a cross-rider API response.
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    display_name: Mapped[str] = mapped_column(String(100))
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=5.00)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), default=Gender.UNDISCLOSED)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED
    )

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED
