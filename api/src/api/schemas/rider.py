"""API-facing rider schemas.

`MaskedRiderProfile` is the ONLY view of a rider ever exposed to their matched partner
(Constitution Principle I) — it intentionally has no `phone_number` or `email` field. Never add
one; if a future feature needs richer identity info, expose it through a separate,
explicitly-reviewed schema, not this one.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from api.src.models.kyc_document import KycStatus
from api.src.models.rider import Gender, VerificationStatus


class MaskedRiderProfile(BaseModel):
    display_name: str
    photo_url: str | None
    rating: float


class OtpRequestIn(BaseModel):
    phone_number: str


class OtpRequestOut(BaseModel):
    rider_id: uuid.UUID
    # ponytail: no real SMS provider in MVP (see verification_service.OtpService) — the code is
    # handed back directly so the flow is testable end-to-end. Remove this field the moment a
    # real SMS gateway is wired in; never ship it to a production build.
    # None once a real SMS provider is configured (prod) — never leak the real code over the
    # wire. Only populated by the in-memory dev fallback (see OtpService.request_otp).
    debug_otp_code: str | None = None


class OtpConfirmIn(BaseModel):
    phone_number: str
    code: str


class OtpConfirmOut(BaseModel):
    rider_id: uuid.UUID
    needs_kyc: bool
    needs_profile: bool


class ProfileIn(BaseModel):
    display_name: str
    gender: Gender = Gender.UNDISCLOSED
    photo_url: str


class RiderOut(BaseModel):
    id: uuid.UUID
    display_name: str
    verification_status: VerificationStatus

    model_config = {"from_attributes": True}


class KycSubmitIn(BaseModel):
    pan_number: str
    name_on_document: str


class KycStatusOut(BaseModel):
    status: KycStatus
    pan_number_last4: str
    verified_at: datetime | None
    rejection_reason: str | None

    model_config = {"from_attributes": True}


class RiderProfileOut(BaseModel):
    """Full self-profile view (Profile/Account page) — still never exposed to a matched
    partner; that's `MaskedRiderProfile`'s job."""

    id: uuid.UUID
    display_name: str
    photo_url: str | None
    rating: float
    verification_status: VerificationStatus

    model_config = {"from_attributes": True}


class RiderStatsOut(BaseModel):
    """Home dashboard stats (Feature 004, page 06) — replaces the old `—` placeholders."""

    rides_shared: int
    total_saved: float


class ActiveActivityOut(BaseModel):
    """Home dashboard (Feature 004): lets a rider resume wherever they left off — a pending
    match, a ready/booked ride, or a still-open intent — without needing to keep local state
    from the screen that created it (e.g. after an app restart, or for pre-seeded demo data)."""

    intent_id: uuid.UUID | None = None
    intent_status: str | None = None
    match_id: uuid.UUID | None = None
    match_status: str | None = None
    ride_id: uuid.UUID | None = None
    ride_status: str | None = None
    # Populated once a match exists, so Home's "Active ride"/"Match found" card can show the
    # actual route + co-rider name (mockups/board.html page 06) instead of a generic status line.
    route_origin: str | None = None
    route_destination: str | None = None
    co_rider_name: str | None = None
    # Coarse booking-progress estimate for the "Active ride" progress bar, derived from
    # ride_status (there is no live GPS feed for the cab leg in this MVP).
    progress_percent: int | None = None

