"""PAN/KYC verification service (Feature 004).

Mirrors the existing `verification_service.py` MVP pattern: no real PAN-verification vendor is
wired in yet, so `submit_kyc` auto-verifies immediately instead of sitting in a reviewer queue.

ponytail: auto-verifying here (no real PAN-registry lookup) is the same explicit MVP shortcut as
`approve_id_check` in `verification_service.py` — swap for a real verification provider (e.g. an
Aadhaar/PAN e-KYC API) before a real launch, gating on `KycDocument.status` instead of
auto-approving.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from api.src.models.kyc_document import DocumentType, KycDocument, KycStatus
from api.src.models.rider import Rider, VerificationStatus
from api.src.services.encryption import encrypt

logger = logging.getLogger(__name__)


def submit_kyc(rider: Rider, pan_number: str, name_on_document: str) -> KycDocument:
    pan_number = pan_number.strip().upper()
    doc = KycDocument(
        id=uuid.uuid4(),
        rider_id=rider.id,
        document_type=DocumentType.PAN,
        pan_number_encrypted=encrypt(pan_number),
        pan_number_last4=pan_number[-4:],
        pan_name_on_document=name_on_document,
        status=KycStatus.PENDING,
    )
    rider.verification_status = VerificationStatus.PENDING

    # ponytail: auto-verify, see module docstring — no real PAN registry integration yet.
    doc.status = KycStatus.VERIFIED
    doc.verified_at = datetime.now(timezone.utc)
    rider.verification_status = VerificationStatus.VERIFIED

    logger.info("kyc.submitted rider_id=%s status=%s", rider.id, doc.status)
    return doc
