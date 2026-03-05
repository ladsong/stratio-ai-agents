from __future__ import annotations

import os

from fastapi import FastAPI
from redis import Redis
from sqlalchemy import text
from sqlalchemy import create_engine


app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    database_url = os.environ["DATABASE_URL"]
    redis_url = os.environ["REDIS_URL"]

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    r = Redis.from_url(redis_url)
    r.ping()

    return {"status": "ready"}
