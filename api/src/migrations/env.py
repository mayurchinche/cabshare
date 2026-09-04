"""Alembic environment wired to the SQLAlchemy models package (`api.src.models`).

Autogeneration compares the DB against `Base.metadata`, which every model in
`api/src/models/` registers with on import.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from api.src.models.base import Base

# ponytail: import models so they register on Base.metadata; add new modules here
from api.src.models import (  # noqa: F401,E402
    rider,
    ride_intent,
    match,
    ride,
    kyc_document,
    station,
    train,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Env var overrides alembic.ini's dev-default URL (same var the running app reads via
# api/src/db.py) so migrations always target whatever DB the deployment actually points at
# (e.g. Railway's Postgres in prod) instead of silently hitting the local dev default.
_env_db_url = os.getenv("CABSHARE_DATABASE_URL")
if _env_db_url:
    # Same normalization as api/src/db.py: managed providers (Render/Railway) often hand out a
    # bare "postgresql://" URL, but we install psycopg v3, not psycopg2.
    if _env_db_url.startswith("postgresql://"):
        _env_db_url = _env_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    config.set_main_option("sqlalchemy.url", _env_db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
