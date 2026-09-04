"""Pydantic schema for the /places/search endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class PlaceOut(BaseModel):
    display_name: str
    latitude: float
    longitude: float
