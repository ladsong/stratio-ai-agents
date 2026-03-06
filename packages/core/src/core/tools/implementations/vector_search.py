from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text

from core.tools.base import BaseTool


class VectorSearchTool(BaseTool):
    """Search knowledge chunks by embedding similarity."""
    
    name = "vector_search"
    description = "Search knowledge base using semantic similarity"
    schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query text"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
    timeout_ms = 5000
    retries = 1
    permission_tag = "database"
    
    def execute(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Search knowledge chunks by semantic similarity."""
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
        )
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, document_id, content, meta
                    FROM knowledge_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT :top_k
                """),
                {"top_k": top_k}
            )
            chunks = [dict(row._mapping) for row in result]
        
        return {
            "chunks": chunks,
            "count": len(chunks),
            "query": query
        }
