from __future__ import annotations

import os

from redis import Redis
from rq import Queue


def get_queue() -> Queue:
    """Get the RQ queue for job enqueuing."""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(redis_url)
    queue_name = os.environ.get("RQ_QUEUE_NAME", "nanobot-runs")
    return Queue(queue_name, connection=redis_conn)
