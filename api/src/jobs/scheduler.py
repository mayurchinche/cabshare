"""APScheduler wiring for background matching jobs (T023, T024).

Registered from `main.py`'s FastAPI lifespan so the jobs only run alongside the API process.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from api.src.jobs.intent_expiry_job import POLL_INTERVAL_SECONDS as EXPIRY_INTERVAL_SECONDS
from api.src.jobs.intent_expiry_job import run_intent_expiry_pass
from api.src.jobs.matching_window_job import POLL_INTERVAL_SECONDS as MATCHING_INTERVAL_SECONDS
from api.src.jobs.matching_window_job import run_matching_window_pass


def build_scheduler(session_factory: sessionmaker) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    def _matching_tick() -> None:
        with session_factory() as db:
            run_matching_window_pass(db)

    def _expiry_tick() -> None:
        with session_factory() as db:
            run_intent_expiry_pass(db)

    scheduler.add_job(_matching_tick, "interval", seconds=MATCHING_INTERVAL_SECONDS, id="matching_window_job")
    scheduler.add_job(_expiry_tick, "interval", seconds=EXPIRY_INTERVAL_SECONDS, id="intent_expiry_job")
    return scheduler
