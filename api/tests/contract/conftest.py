"""Shared test-DB wiring for contract tests: a single SQLite engine + `get_db` override so
every contract test file operates against the same overridden dependency (avoids two modules
clobbering `app.dependency_overrides` with separate engines).
"""

from __future__ import annotations

import os

os.environ.setdefault("CABSHARE_ENABLE_SCHEDULER", "false")
os.environ.setdefault("CABSHARE_DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.src.db import get_db
from api.src.main import app
from api.src.models.base import Base

engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_session():
    return TestingSessionLocal
