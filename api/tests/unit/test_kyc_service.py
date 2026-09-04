"""Unit tests for Feature 004's PAN/KYC encryption + service (ponytail: minimal but real
round-trip + never-plaintext checks, not a full test suite)."""

from api.src.models.kyc_document import KycStatus
from api.src.models.rider import Rider, VerificationStatus
from api.src.services.encryption import decrypt, encrypt
from api.src.services.kyc_service import submit_kyc


def test_encrypt_decrypt_round_trip():
    plaintext = "ABCDE1234F"
    blob = encrypt(plaintext)
    assert blob != plaintext.encode("utf-8")  # never stored as plaintext bytes
    assert decrypt(blob) == plaintext


def test_encrypt_is_nondeterministic():
    # Same input MUST produce different ciphertext each call (random nonce) — otherwise two
    # riders sharing a PAN digit pattern would leak equality via ciphertext comparison.
    blob_a = encrypt("ABCDE1234F")
    blob_b = encrypt("ABCDE1234F")
    assert blob_a != blob_b


def test_submit_kyc_never_stores_plaintext_pan_and_verifies_rider():
    rider = Rider(display_name="", phone_number="+911234567890")
    doc = submit_kyc(rider, "abcde1234f", "Aditi Sharma")

    assert doc.pan_number_last4 == "234F"
    assert b"ABCDE1234F" not in doc.pan_number_encrypted
    assert decrypt(doc.pan_number_encrypted) == "ABCDE1234F"
    assert doc.status == KycStatus.VERIFIED  # ponytail auto-verify, see kyc_service docstring
    assert rider.verification_status == VerificationStatus.VERIFIED
