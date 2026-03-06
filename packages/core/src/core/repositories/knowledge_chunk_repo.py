from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class KnowledgeChunkRepository:
    """Repository for knowledge chunk operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, chunk_id: str, document_id: str, content: str, embedding: list[float] | None = None, meta: dict | None = None):
        """Create a new knowledge chunk."""
        import json
        
        if embedding:
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            self.db.execute(
                text("""
                    INSERT INTO knowledge_chunks (id, document_id, content, embedding, meta, created_at, updated_at)
                    VALUES (:id, :document_id, :content, CAST(:embedding AS vector), CAST(:meta AS jsonb), NOW(), NOW())
                """),
                {
                    "id": chunk_id,
                    "document_id": document_id,
                    "content": content,
                    "embedding": embedding_str,
                    "meta": json.dumps(meta or {})
                }
            )
        else:
            self.db.execute(
                text("""
                    INSERT INTO knowledge_chunks (id, document_id, content, meta, created_at, updated_at)
                    VALUES (:id, :document_id, :content, CAST(:meta AS jsonb), NOW(), NOW())
                """),
                {
                    "id": chunk_id,
                    "document_id": document_id,
                    "content": content,
                    "meta": json.dumps(meta or {})
                }
            )
        self.db.commit()
    
    def get_by_id(self, chunk_id: str):
        """Get a chunk by ID."""
        result = self.db.execute(
            text("SELECT * FROM knowledge_chunks WHERE id = :id"),
            {"id": chunk_id}
        )
        return result.fetchone()
    
    def list_by_document(self, document_id: str, limit: int = 100):
        """List chunks for a document."""
        result = self.db.execute(
            text("""
                SELECT id, document_id, content, 
                       CASE WHEN embedding IS NOT NULL THEN true ELSE false END as has_embedding,
                       meta, created_at, updated_at
                FROM knowledge_chunks
                WHERE document_id = :document_id
                ORDER BY created_at ASC
                LIMIT :limit
            """),
            {"document_id": document_id, "limit": limit}
        )
        return result.fetchall()
    
    def search_by_embedding(self, query_embedding: list[float], top_k: int = 5):
        """Search chunks by embedding similarity."""
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        result = self.db.execute(
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
        return result.fetchall()
