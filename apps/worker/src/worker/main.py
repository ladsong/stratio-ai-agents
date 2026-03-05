from __future__ import annotations

import os
import time

from redis import Redis


def main() -> None:
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    r = Redis.from_url(redis_url)

    while True:
        try:
            r.ping()
            print("worker: alive")
        except Exception as e:
            print(f"worker: error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()
