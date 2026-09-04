"""RailRadar (https://railradar.in) implementation of `TrainDataProvider` (Feature 003 —
unblocked by user-provided paid API key, see session notes). Free-sandbox tier is rate-limited
to 1,000 requests/month; callers MUST go through `TrainLiveStatusService`'s DB cache rather than
calling this directly on every screen render.
"""

from __future__ import annotations

import ssl
from datetime import date

import httpx
import truststore

from api.src.config import train_data_config
from api.src.services.train_data.base import LiveStatus, RouteStop, TrainDataProvider, TrainSearchResult


class RailRadarUnavailableError(RuntimeError):
    """Raised when RailRadar has no key configured or the request fails (network/4xx/5xx)."""


class RailRadarProvider(TrainDataProvider):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or train_data_config.api_key
        self._base_url = base_url or train_data_config.base_url

    def _client(self) -> httpx.Client:
        if not self._api_key:
            raise RailRadarUnavailableError("CABSHARE_RAILRADAR_API_KEY is not configured")
        # Use the OS-native trust store rather than the bundled certifi CA list — this
        # environment's outbound HTTPS is intercepted by a locally-trusted root that macOS
        # trusts (curl works) but Python's default bundle does not; disabling verification
        # entirely would be the wrong fix for a real partner API call.
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return httpx.Client(
            base_url=self._base_url,
            headers={"x-api-key": self._api_key},
            timeout=10.0,
            verify=ssl_context,
        )

    def search_between(
        self, from_station_code: str, to_station_code: str, travel_date: date | None = None
    ) -> list[TrainSearchResult]:
        params = {"date": travel_date.isoformat()} if travel_date else {}
        with self._client() as client:
            try:
                resp = client.get(
                    f"/trains/between/{from_station_code}/{to_station_code}", params=params
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise RailRadarUnavailableError(str(exc)) from exc
        payload = resp.json()
        if not payload.get("success"):
            raise RailRadarUnavailableError(f"RailRadar returned success=false: {payload}")
        results: list[TrainSearchResult] = []
        for entry in payload["data"].get("trains", []):
            train = entry["train"]
            frm, to = entry["from"], entry["to"]
            results.append(
                TrainSearchResult(
                    train_number=train["number"],
                    train_name=train["name"],
                    from_stop=RouteStop(
                        station_code=frm["code"],
                        station_name=frm["name"],
                        scheduled_arrival=frm.get("arrival"),
                        scheduled_departure=frm.get("departure"),
                        sequence=frm.get("sequence", 0),
                        day=frm.get("day", 0),
                    ),
                    to_stop=RouteStop(
                        station_code=to["code"],
                        station_name=to["name"],
                        scheduled_arrival=to.get("arrival"),
                        scheduled_departure=to.get("departure"),
                        sequence=to.get("sequence", 0),
                        day=to.get("day", 0),
                    ),
                    distance_km=entry.get("distance"),
                    duration_minutes=entry.get("duration"),
                )
            )
        return results

    def get_live_status(self, train_number: str, travel_date: date) -> LiveStatus:
        with self._client() as client:
            try:
                resp = client.get(
                    f"/trains/{train_number}/live", params={"date": travel_date.isoformat()}
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise RailRadarUnavailableError(str(exc)) from exc
        payload = resp.json()
        if not payload.get("success"):
            raise RailRadarUnavailableError(f"RailRadar returned success=false: {payload}")
        data = payload["data"]
        current = data.get("currentLocation") or {}
        next_halt = data.get("nextHalt") or {}
        return LiveStatus(
            train_number=train_number,
            travel_date=travel_date,
            status=data.get("status", "unknown"),
            delay_minutes=current.get("delayMinutes"),
            last_station_code=current.get("stationCode"),
            last_station_name=current.get("stationName"),
            next_station_code=next_halt.get("stationCode"),
            next_station_name=next_halt.get("stationName"),
            segment_progress=current.get("segmentProgress"),
            raw_payload=data,
        )
