from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class ToolCallRepository:
    """Repository for tool call operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, tool_call_id: str):
        """Get a tool call by ID."""
        result = self.db.execute(
            text("SELECT * FROM tool_calls WHERE id = :id"),
            {"id": tool_call_id}
        )
        return result.fetchone()
    
    def list_by_run(self, run_id: str, limit: int = 100):
        """List tool calls for a run."""
        result = self.db.execute(
            text("""
                SELECT * FROM tool_calls
                WHERE run_id = :run_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"run_id": run_id, "limit": limit}
        )
        return result.fetchall()
