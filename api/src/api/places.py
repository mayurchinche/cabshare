"""Place search API — free real-world address/POI search via Photon (komoot's public OSM
geocoder; no API key required).

This is the "standard cab-app location picker" data source for a rider's exact drop-off point
(distinct from `/stations/search`, which only covers railway stations) — same free-tier
philosophy as the RailRadar/`datameet` choices elsewhere in this API.

ponytail: previously used Nominatim directly, but its public instance actively rate-limits/
blocks shared cloud-provider egress IPs (Render, AWS, etc.) once aggregate traffic crosses its
fair-use threshold — this surfaced in production as "no places found" for every search. Photon
is built by komoot specifically for this searchable-as-you-type use case and doesn't impose
that same per-IP block for normal server traffic.
"""

from __future__ import annotations

import ssl

import httpx
import truststore
from fastapi import APIRouter, HTTPException, Query

from api.src.api.schemas.place import PlaceOut

router = APIRouter(prefix="/places", tags=["places"])

PHOTON_URL = "https://photon.komoot.io/api/"
# Photon blocks httpx's default User-Agent string outright (403) — any descriptive/browser-like
# UA works; unlike Nominatim this isn't a fair-use identification requirement, just an
# anti-bot heuristic on their end.
USER_AGENT = "CabShare/1.0 (+https://github.com/mayurchinche/cabshare)"
# Bias results toward India (roughly the country's geographic center) since this app only
# operates there; Photon has no countrycodes filter, so we bias + post-filter by countrycode.
INDIA_BIAS_LAT = 20.5937
INDIA_BIAS_LON = 78.9629


def _display_name(props: dict) -> str:
    parts = [
        props.get("name"),
        props.get("street"),
        props.get("city"),
        props.get("state"),
        props.get("country"),
    ]
    return ", ".join(p for p in parts if p)


@router.get("/search", response_model=list[PlaceOut])
def search_places(
    q: str = Query(..., min_length=3, description="Free-text address or place name"),
    limit: int = Query(8, le=15),
) -> list[PlaceOut]:
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    try:
        with httpx.Client(timeout=8.0, verify=ssl_context) as client:
            resp = client.get(
                PHOTON_URL,
                params={
                    "q": q,
                    "limit": limit * 2,  # over-fetch since we post-filter to India-only below
                    "lat": INDIA_BIAS_LAT,
                    "lon": INDIA_BIAS_LON,
                },
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Place search unavailable: {exc}") from exc

    features = resp.json().get("features", [])
    results: list[PlaceOut] = []
    for entry in features:
        props = entry.get("properties", {})
        if props.get("countrycode") != "IN":
            continue
        lon, lat = entry["geometry"]["coordinates"]
        display_name = _display_name(props)
        if not display_name:
            continue
        results.append(PlaceOut(display_name=display_name, latitude=lat, longitude=lon))
        if len(results) >= limit:
            break
    return results
