"""KycDocument model (Feature 004 DATABASE.md §kyc_documents).

One row per verification attempt (audit trail, not overwritten). `pan_number_encrypted` is the
ONLY place PAN plaintext-adjacent data may be decrypted from — see `services/encryption.py` and
`services/kyc_service.py`. `pan_number_last4` is the sole field safe to ever return to the owning
rider's own profile view (never to a matched partner).
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from api.src.models.base import Base


class DocumentType(str, enum.Enum):
    PAN = "pan"


class KycStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class KycDocument(Base):
    __tablename__ = "kyc_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("riders.id"), index=True)

    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.PAN)
    pan_number_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    pan_number_last4: Mapped[str] = mapped_column(String(4))
    pan_name_on_document: Mapped[str] = mapped_column(String(100))

    status: Mapped[KycStatus] = mapped_column(Enum(KycStatus), default=KycStatus.PENDING)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    rejection_reason: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
