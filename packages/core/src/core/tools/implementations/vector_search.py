from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text

from core.knowledge.embeddings import StubEmbeddingGenerator
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
        
        # Generate query embedding
        embedding_generator = StubEmbeddingGenerator(dimension=1536)
        query_embedding = embedding_generator.generate([query])[0]
        
        # Convert embedding to string format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        with engine.connect() as conn:
            # Try embedding-based search first
            result = conn.execute(
                text("""
                    SELECT c.id, c.document_id, c.content, c.meta,
                           d.title as document_title,
                           c.embedding <-> CAST(:query_embedding AS vector) as distance
                    FROM knowledge_chunks c
                    JOIN knowledge_documents d ON c.document_id = d.id
                    WHERE c.embedding IS NOT NULL
                    ORDER BY c.embedding <-> CAST(:query_embedding AS vector)
                    LIMIT :top_k
                """),
                {"query_embedding": embedding_str, "top_k": top_k}
            )
            chunks = [dict(row._mapping) for row in result]
            
            # If no results with embeddings, fall back to text search
            if not chunks:
                result = conn.execute(
                    text("""
                        SELECT c.id, c.document_id, c.content, c.meta,
                               d.title as document_title
                        FROM knowledge_chunks c
                        JOIN knowledge_documents d ON c.document_id = d.id
                        WHERE c.content ILIKE :query_pattern
                        LIMIT :top_k
                    """),
                    {"query_pattern": f"%{query}%", "top_k": top_k}
                )
                chunks = [dict(row._mapping) for row in result]
        
        return {
            "chunks": chunks,
            "count": len(chunks),
            "query": query,
            "search_type": "embedding" if chunks and "distance" in chunks[0] else "text"
        }
