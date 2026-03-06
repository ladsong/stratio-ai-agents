from __future__ import annotations

import os
import uuid
from typing import Any

from sqlalchemy import create_engine, text

from core.tools.base import BaseTool


class ArtifactWriterTool(BaseTool):
    """Create artifact records in the database."""
    
    name = "artifact_writer"
    description = "Create an artifact record linked to a run"
    schema = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "ID of the run to link the artifact to"
            },
            "artifact_type": {
                "type": "string",
                "description": "Type of artifact (e.g., strategy_document, analysis_report)"
            },
            "content": {
                "type": "string",
                "description": "Content of the artifact"
            },
            "meta": {
                "type": "object",
                "description": "Additional metadata for the artifact"
            }
        },
        "required": ["run_id", "artifact_type", "content"]
    }
    timeout_ms = 5000
    retries = 1
    permission_tag = "safe"
    
    def execute(self, run_id: str, artifact_type: str, content: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create an artifact record."""
        artifact_id = str(uuid.uuid4())
        
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
        )
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            import json
            conn.execute(
                text("""
                    INSERT INTO artifacts (id, run_id, artifact_type, content, meta, created_at, updated_at)
                    VALUES (:id, :run_id, :artifact_type, :content, CAST(:meta AS jsonb), NOW(), NOW())
                """),
                {
                    "id": artifact_id,
                    "run_id": run_id,
                    "artifact_type": artifact_type,
                    "content": content,
                    "meta": json.dumps(meta or {})
                }
            )
            conn.commit()
        
        return {
            "artifact_id": artifact_id,
            "run_id": run_id,
            "artifact_type": artifact_type
        }
