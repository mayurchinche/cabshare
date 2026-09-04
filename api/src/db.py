"""Shared DB engine/session — split out from main.py to avoid circular imports between
main.py (which registers routers) and the router modules (which need `get_db`)."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "CABSHARE_DATABASE_URL", "postgresql://cabshare:cabshare@localhost:5432/cabshare"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
