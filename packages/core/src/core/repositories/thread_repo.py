from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.models import Thread


class ThreadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, thread_id: str, meta: Optional[dict] = None) -> Thread:
        thread = Thread(id=thread_id, meta=meta)
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread

    def get_by_id(self, thread_id: str) -> Optional[Thread]:
        return self.db.query(Thread).filter(Thread.id == thread_id).first()
