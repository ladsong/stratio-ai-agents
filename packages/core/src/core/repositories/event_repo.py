from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.models import Event


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        event_id: str,
        thread_id: str,
        role: str,
        content: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        meta: Optional[dict] = None,
    ) -> Event:
        event = Event(
            id=event_id,
            thread_id=thread_id,
            role=role,
            content=content,
            idempotency_key=idempotency_key,
            meta=meta,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Event]:
        return self.db.query(Event).filter(Event.idempotency_key == idempotency_key).first()

    def list_by_thread(self, thread_id: str, limit: int = 100) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(Event.thread_id == thread_id)
            .order_by(Event.created_at.desc())
            .limit(limit)
            .all()
        )
