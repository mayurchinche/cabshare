# Build context MUST be the repo root (not api/): imports are `api.src.*` and alembic's
# script_location is `api/src/migrations`, both relative to the repo root — see api/alembic.ini.
# This mirrors exactly how the app is already run locally (uvicorn api.src.main:app from repo
# root with PYTHONPATH=repo root), so no packaging/setuptools layout changes were needed.
# Railway service config: Root Directory = "." (repo root), Dockerfile Path = "api/Dockerfile".
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install runtime deps straight from pyproject's dependency list (no package build/install of
# the app itself — it's run as plain source, same as local dev) so this stays in sync with
# pyproject.toml without duplicating the dependency list here.
COPY api/pyproject.toml api/pyproject.toml
RUN python -c "\
import subprocess, tomllib; \
deps = tomllib.load(open('api/pyproject.toml', 'rb'))['project']['dependencies']; \
subprocess.check_call(['pip', 'install', '--no-cache-dir', *deps])"

COPY api api

ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
EXPOSE 8000

# Railway injects $PORT. Runs from /app (repo root) so `api.src.*` imports and alembic's
# relative script_location both resolve correctly, exactly like local dev.
CMD alembic -c api/alembic.ini upgrade head && \
    uvicorn api.src.main:app --host 0.0.0.0 --port ${PORT:-8000}
