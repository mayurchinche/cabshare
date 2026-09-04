"""Contract test for the station-search endpoint (Feature 003, station-picker-only scope)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.src.models.station import Station


def _seed_stations(db_session) -> None:
    db = db_session()
    db.add_all(
        [
            Station(station_code="PUNE", name="PUNE JN", state="Maharashtra", latitude=18.53, longitude=73.87),
            Station(station_code="NDLS", name="NEW DELHI", state="Delhi", latitude=28.64, longitude=77.22),
        ]
    )
    db.commit()
    db.close()


def test_search_by_name_prefix(client: TestClient, db_session) -> None:
    _seed_stations(db_session)
    resp = client.get("/stations/search", params={"q": "PUNE"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["station_code"] == "PUNE"


def test_search_by_code_prefix(client: TestClient, db_session) -> None:
    _seed_stations(db_session)
    resp = client.get("/stations/search", params={"q": "NDL"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "NEW DELHI"


def test_search_requires_min_length(client: TestClient) -> None:
    resp = client.get("/stations/search", params={"q": "a"})
    assert resp.status_code == 422
