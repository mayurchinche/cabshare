"""Place search API — free real-world address/POI search via OpenStreetMap Nominatim (no API
key required; a `User-Agent` header is required by Nominatim's usage policy in place of one).

This is the "standard cab-app location picker" data source for a rider's exact drop-off point
(distinct from `/stations/search`, which only covers railway stations) — same free-tier
philosophy as the RailRadar/`datameet` choices elsewhere in this API.
"""

from __future__ import annotations

import ssl

import httpx
import truststore
from fastapi import APIRouter, HTTPException, Query

from api.src.api.schemas.place import PlaceOut

router = APIRouter(prefix="/places", tags=["places"])

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim's usage policy requires a descriptive User-Agent identifying the application.
USER_AGENT = "CabShare/1.0 (ride-sharing MVP; contact via app support)"


@router.get("/search", response_model=list[PlaceOut])
def search_places(
    q: str = Query(..., min_length=3, description="Free-text address or place name"),
    limit: int = Query(8, le=15),
) -> list[PlaceOut]:
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    try:
        with httpx.Client(timeout=8.0, verify=ssl_context) as client:
            resp = client.get(
                NOMINATIM_URL,
                params={
                    "q": q,
                    "format": "jsonv2",
                    "limit": limit,
                    "countrycodes": "in",  # India-only, matches this app's scope
                },
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Place search unavailable: {exc}") from exc

    return [
        PlaceOut(
            display_name=entry["display_name"],
            latitude=float(entry["lat"]),
            longitude=float(entry["lon"]),
        )
        for entry in resp.json()
    ]
