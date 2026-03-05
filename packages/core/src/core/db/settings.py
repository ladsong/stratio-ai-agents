from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
