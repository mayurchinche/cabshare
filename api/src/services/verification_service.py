"""Identity verification: phone OTP + photo/ID check.

MVP implementation stubs the actual SMS/ID-check providers behind simple functions so the
gating logic (Constitution Principle II / FR-011) can be built and tested now, with a real
provider swapped in later without touching callers.
"""

from __future__ import annotations

import logging
import os

from api.src.models.rider import Rider, VerificationStatus

# Never log phone_number/email — only opaque rider IDs and status transitions.
logger = logging.getLogger(__name__)


class VerificationError(Exception):
    """Raised when a rider tries to act without being verified."""


class OtpService:
    """OTP delivery: real SMS via Twilio's plain Messaging API (works on a trial account's free
    credit — Twilio Verify needs a paid/upgraded account, so we generate and store the code
    ourselves and just send it as a text) when TWILIO_* env vars are set (prod); else an
    in-memory dev fallback whose code is echoed back to the caller for local/emulator testing
    (see riders.py's debug_otp_code)."""

    def __init__(self) -> None:
        self._codes: dict[str, str] = {}
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self._from_number = os.getenv("TWILIO_FROM_NUMBER")
        self._twilio_client = None
        if account_sid and auth_token and self._from_number:
            from twilio.rest import Client  # imported lazily: optional dep, only needed in prod

            self._twilio_client = Client(account_sid, auth_token)

    @property
    def uses_real_sms(self) -> bool:
        return self._twilio_client is not None

    # ponytail: fixed OTP for all users while Twilio is unpaid/broken. Revert to
    # random once a paid Twilio (or other SMS provider) is wired back in.
    _FIXED_CODE = "5484"

    def request_otp(self, phone_number: str) -> str | None:
        code = self._FIXED_CODE
        self._codes[phone_number] = code
        if self._twilio_client is not None:
            try:
                self._twilio_client.messages.create(
                    body=f"Your CabShare verification code is {code}",
                    from_=self._from_number,
                    to=phone_number,
                )
                logger.info("otp.requested via=twilio")
                return None
            except Exception:
                # ponytail: Twilio trial accounts reject custom SMS bodies/unverified numbers.
                # Fall back to on-screen code (fine for friend-testing) instead of a 500.
                # Upgrade to a paid Twilio account to restore real SMS delivery.
                logger.exception("otp.twilio_send_failed, falling back to debug code")
        logger.info("otp.requested via=debug")
        return code

    def confirm_otp(self, phone_number: str, code: str) -> bool:
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
