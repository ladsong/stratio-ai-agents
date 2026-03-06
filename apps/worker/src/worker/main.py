from __future__ import annotations

import logging
import os
import sys

from redis import Redis
from rq import Worker, Queue


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)


def main() -> None:
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    queue_name = os.environ.get("RQ_QUEUE_NAME", "nanobot-runs")
    
    logger.info(f"Starting RQ worker for queue: {queue_name}")
    logger.info(f"Redis URL: {redis_url}")
    
    redis_conn = Redis.from_url(redis_url)
    
    try:
        redis_conn.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    
    queue = Queue(queue_name, connection=redis_conn)
    
    worker = Worker([queue], connection=redis_conn)
    
    logger.info("Worker started, listening for jobs...")
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
