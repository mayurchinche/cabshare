"""Unit tests for verification_service (FR-011, Constitution Principle II)."""

import uuid

import pytest

from api.src.models.rider import Gender, Rider, VerificationStatus
from api.src.services.verification_service import (
    OtpService,
    VerificationError,
    approve_id_check,
    require_verified,
    submit_id_check,
)


def make_rider(status: VerificationStatus = VerificationStatus.UNVERIFIED) -> Rider:
    return Rider(
        id=uuid.uuid4(),
        phone_number="+919999999999",
        email=None,
        display_name="Test R.",
        gender=Gender.UNDISCLOSED,
        verification_status=status,
    )


def test_unverified_rider_cannot_post_or_accept_intent():
    rider = make_rider()
    with pytest.raises(VerificationError):
        require_verified(rider)


def test_verified_rider_passes_gate():
    rider = make_rider(status=VerificationStatus.VERIFIED)
    require_verified(rider)  # should not raise


def test_otp_confirm_matches_requested_code():
    otp = OtpService()
    otp.request_otp("+919999999999")
    code = otp._codes["+919999999999"]
    assert otp.confirm_otp("+919999999999", code) is True
    assert otp.confirm_otp("+919999999999", "000000") is False


def test_full_verification_flow_gates_then_passes():
    rider = make_rider()
    with pytest.raises(VerificationError):
        require_verified(rider)

    submit_id_check(rider, photo_url="https://example.com/id.jpg")
    assert rider.verification_status == VerificationStatus.PENDING
    with pytest.raises(VerificationError):
        require_verified(rider)

    approve_id_check(rider)
    assert rider.verification_status == VerificationStatus.VERIFIED
    require_verified(rider)  # should not raise
