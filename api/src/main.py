"""FastAPI app entrypoint: DB session dependency + router registration."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.src.db import SessionLocal, engine, get_db  # noqa: F401  (re-exported for callers)
from api.src.jobs.scheduler import build_scheduler

# Root logging config lives here (app entrypoint) so every module's `getLogger(__name__)` call
# (matching_service, fare_service, jobs, etc. — T046) actually reaches stdout. Uvicorn only
# configures its own "uvicorn.*" loggers by default; without this, our INFO logs are silently
# dropped at the root logger's default WARNING level.
logging.basicConfig(
    level=os.getenv("CABSHARE_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

__all__ = ["app", "create_app", "get_db"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Env-gated so unit/contract tests that import create_app() don't spin up background
    # DB-polling jobs; the real deployment sets this to "true" (or leaves the default).
    scheduler = None
    if os.getenv("CABSHARE_ENABLE_SCHEDULER", "true").lower() == "true":
        scheduler = build_scheduler(SessionLocal)
        scheduler.start()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="CabShare Ride Pairing API", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        # Used by Railway's healthcheck to gate deploy rollover; no DB round-trip on purpose
        # (keep it cheap/independent so a slow DB doesn't false-fail a healthy process).
        return {"status": "ok"}

    # Routers registered here as each is implemented (intents, matches, rides).
    from api.src.api.intents import router as intents_router
    from api.src.api.matches import router as matches_router
    from api.src.api.riders import router as riders_router
    from api.src.api.rides import router as rides_router
    from api.src.api.places import router as places_router
    from api.src.api.stations import router as stations_router
    from api.src.api.trains import router as trains_router

    app.include_router(riders_router)
    app.include_router(intents_router)
    app.include_router(matches_router)
    app.include_router(rides_router)
    app.include_router(stations_router)
    app.include_router(trains_router)
    app.include_router(places_router)

    return app


app = create_app()
