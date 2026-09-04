"""MVP auth stand-in.

ponytail: real auth (JWT/session from the mobile app's login flow) is out of scope for the
matching-MVP; a verified rider's own ID is passed via the `X-Rider-Id` header. Swap this for a
real auth dependency behind the same `get_current_rider_id` signature once auth is built.
"""

from __future__ import annotations

import uuid

from fastapi import Header, HTTPException


def get_current_rider_id(x_rider_id: uuid.UUID = Header(...)) -> uuid.UUID:
    if not x_rider_id:
        raise HTTPException(status_code=401, detail="X-Rider-Id header required")
    return x_rider_id
