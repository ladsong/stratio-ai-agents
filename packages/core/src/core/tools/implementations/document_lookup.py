from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text

from core.tools.base import BaseTool


class DocumentLookupTool(BaseTool):
    """Retrieve a document by ID from the knowledge base."""
    
    name = "document_lookup"
    description = "Retrieve a specific document by its ID"
    schema = {
        "type": "object",
        "properties": {
            "document_id": {
                "type": "string",
                "description": "ID of the document to retrieve"
            }
        },
        "required": ["document_id"]
    }
    timeout_ms = 2000
    retries = 1
    permission_tag = "safe"
    
    def execute(self, document_id: str) -> dict[str, Any]:
        """Retrieve a document by ID."""
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
        )
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, title, content, meta, created_at
                    FROM knowledge_documents
                    WHERE id = :document_id
                """),
                {"document_id": document_id}
            )
            row = result.fetchone()
        
        if not row:
            return {
                "found": False,
                "document_id": document_id
            }
        
        return {
            "found": True,
            "document": dict(row._mapping)
        }
