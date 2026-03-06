from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class ToolCallLogger:
    """Logger for tool call execution tracking."""
    
    def __init__(self, db: Session, run_id: str):
        self.db = db
        self.run_id = run_id
        self.tool_call_id: str | None = None
        self.start_time: float | None = None
    
    def start(self, tool_name: str, inputs: dict[str, Any]) -> str:
        """Start logging a tool call."""
        self.tool_call_id = str(uuid.uuid4())
        self.start_time = time.time()
        
        logger.info(f"Starting tool call {self.tool_call_id}: {tool_name}")
        
        self.db.execute(
            text("""
                INSERT INTO tool_calls (id, run_id, tool_name, inputs, created_at, updated_at)
                VALUES (:id, :run_id, :tool_name, CAST(:inputs AS jsonb), NOW(), NOW())
            """),
            {
                "id": self.tool_call_id,
                "run_id": self.run_id,
                "tool_name": tool_name,
                "inputs": json.dumps(inputs),
            }
        )
        self.db.commit()
        
        return self.tool_call_id
    
    def complete(self, outputs: dict[str, Any]) -> None:
        """Complete a tool call with success."""
        if not self.tool_call_id or not self.start_time:
            logger.error("Cannot complete tool call: not started")
            return
        
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        logger.info(f"Completed tool call {self.tool_call_id} in {duration_ms}ms")
        
        self.db.execute(
            text("""
                UPDATE tool_calls
                SET outputs = CAST(:outputs AS jsonb), duration_ms = :duration_ms, updated_at = NOW()
                WHERE id = :id
            """),
            {
                "id": self.tool_call_id,
                "outputs": json.dumps(outputs),
                "duration_ms": duration_ms,
            }
        )
        self.db.commit()
    
    def fail(self, error: str) -> None:
        """Complete a tool call with failure."""
        if not self.tool_call_id or not self.start_time:
            logger.error("Cannot fail tool call: not started")
            return
        
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        logger.error(f"Failed tool call {self.tool_call_id} after {duration_ms}ms: {error}")
        
        self.db.execute(
            text("""
                UPDATE tool_calls
                SET error = :error, duration_ms = :duration_ms, updated_at = NOW()
                WHERE id = :id
            """),
            {
                "id": self.tool_call_id,
                "error": error,
                "duration_ms": duration_ms,
            }
        )
        self.db.commit()
