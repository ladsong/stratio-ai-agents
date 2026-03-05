from __future__ import annotations

from sqlalchemy.orm import Session

from core.db.models import GraphRegistry, ToolRegistry


class RegistryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_tools(self) -> list[ToolRegistry]:
        return self.db.query(ToolRegistry).all()

    def list_graphs(self) -> list[GraphRegistry]:
        return self.db.query(GraphRegistry).all()
