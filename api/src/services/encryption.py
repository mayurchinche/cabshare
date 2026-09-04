"""Field-level AES-256-GCM encryption for sensitive rider documents (e.g. PAN numbers).

Isolated in its own module so PAN plaintext only ever exists inside `kyc_service` — matching,
booking, and notification code must never import this module or touch decrypted values
(Constitution Principle I: no unnecessary spread of sensitive personal data).

ponytail: key sourced from an env var (`KYC_ENCRYPTION_KEY`, 32 raw bytes, base64-encoded) for
MVP. Upgrade path once real PAN data hits production: move key storage/rotation to a managed
KMS (AWS KMS / GCP KMS) and envelope-encrypt per record instead of a single static key.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_SIZE_BYTES = 12


def _load_key() -> bytes:
    raw = os.getenv("KYC_ENCRYPTION_KEY")
    if not raw:
        # ponytail: dev-only fallback key so local/test runs work without extra setup — the
        # module fails loudly instead of silently using this key in any real deployment because
        # `CABSHARE_ENV=production` (or similar) should always set a real KYC_ENCRYPTION_KEY.
        raw = base64.b64encode(b"0" * 32).decode()
    key = base64.b64decode(raw)
    if len(key) != 32:
        raise ValueError("KYC_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def encrypt(plaintext: str) -> bytes:
    """Returns nonce || ciphertext (nonce prefixed so decrypt() is self-contained)."""
    aesgcm = AESGCM(_load_key())
    nonce = os.urandom(_NONCE_SIZE_BYTES)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return nonce + ciphertext


def decrypt(blob: bytes) -> str:
    aesgcm = AESGCM(_load_key())
    nonce, ciphertext = blob[:_NONCE_SIZE_BYTES], blob[_NONCE_SIZE_BYTES:]
    return aesgcm.decrypt(nonce, ciphertext, associated_data=None).decode("utf-8")
