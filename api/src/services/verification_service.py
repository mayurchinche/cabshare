"""Identity verification: phone OTP + photo/ID check.

MVP implementation stubs the actual SMS/ID-check providers behind simple functions so the
gating logic (Constitution Principle II / FR-011) can be built and tested now, with a real
provider swapped in later without touching callers.
"""

from __future__ import annotations

import logging
import os
import random

from api.src.models.rider import Rider, VerificationStatus

# Never log phone_number/email — only opaque rider IDs and status transitions.
logger = logging.getLogger(__name__)


class VerificationError(Exception):
    """Raised when a rider tries to act without being verified."""


class OtpService:
    """OTP delivery: real SMS via Twilio Verify when TWILIO_* env vars are set (prod), else an
    in-memory dev fallback whose code is echoed back to the caller for local/emulator testing
    (see riders.py's debug_otp_code). Twilio Verify owns code generation/storage/expiry itself,
    so no local `_codes` bookkeeping is needed on that path."""

    def __init__(self) -> None:
        self._codes: dict[str, str] = {}
        self._verify_service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self._twilio_client = None
        if account_sid and auth_token and self._verify_service_sid:
            from twilio.rest import Client  # imported lazily: optional dep, only needed in prod

            self._twilio_client = Client(account_sid, auth_token)

    @property
    def uses_real_sms(self) -> bool:
        return self._twilio_client is not None

    def request_otp(self, phone_number: str) -> str | None:
        if self._twilio_client is not None:
            self._twilio_client.verify.v2.services(self._verify_service_sid).verifications.create(
                to=phone_number, channel="sms"
            )
            logger.info("otp.requested via=twilio")
            return None
        code = f"{random.randint(0, 999999):06d}"
        self._codes[phone_number] = code
        logger.info("otp.requested via=debug")
        return code

    def confirm_otp(self, phone_number: str, code: str) -> bool:
        if self._twilio_client is not None:
            check = self._twilio_client.verify.v2.services(
                self._verify_service_sid
            ).verification_checks.create(to=phone_number, code=code)
            ok = check.status == "approved"
        else:
            ok = self._codes.get(phone_number) == code
        logger.info("otp.confirm_attempted success=%s", ok)
        return ok


def submit_id_check(rider: Rider, photo_url: str) -> Rider:
    """Record a photo/ID check submission. MVP marks it `pending` for manual review."""
    rider.photo_url = photo_url
    rider.verification_status = VerificationStatus.PENDING
    logger.info("verification.id_submitted rider_id=%s", rider.id)
    return rider


def approve_id_check(rider: Rider) -> Rider:
    """Manual-review approval transition (called by an admin/reviewer action)."""
    rider.verification_status = VerificationStatus.VERIFIED
    logger.info("verification.approved rider_id=%s", rider.id)
    return rider


def reject_id_check(rider: Rider) -> Rider:
    rider.verification_status = VerificationStatus.REJECTED
    logger.info("verification.rejected rider_id=%s", rider.id)
    return rider


def require_verified(rider: Rider) -> None:
    """Gate used by intent-posting/accepting endpoints (FR-011)."""
    if not rider.is_verified:
        logger.warning("verification.gate_blocked rider_id=%s", rider.id)
        raise VerificationError(
            f"Rider {rider.id} must complete verification before posting or accepting an intent"
        )
