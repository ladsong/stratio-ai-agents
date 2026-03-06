from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class KnowledgeDocumentRepository:
    """Repository for knowledge document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, document_id: str, title: str | None, content: str, meta: dict | None = None):
        """Create a new knowledge document."""
        import json
        self.db.execute(
            text("""
                INSERT INTO knowledge_documents (id, title, content, meta, created_at, updated_at)
                VALUES (:id, :title, :content, CAST(:meta AS jsonb), NOW(), NOW())
            """),
            {
                "id": document_id,
                "title": title,
                "content": content,
                "meta": json.dumps(meta or {})
            }
        )
        self.db.commit()
        return self.get_by_id(document_id)
    
    def get_by_id(self, document_id: str):
        """Get a document by ID."""
        result = self.db.execute(
            text("SELECT * FROM knowledge_documents WHERE id = :id"),
            {"id": document_id}
        )
        return result.fetchone()
    
    def list_documents(self, limit: int = 100, offset: int = 0):
        """List documents with pagination."""
        result = self.db.execute(
            text("""
                SELECT * FROM knowledge_documents
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset}
        )
        return result.fetchall()
    
    def count_chunks(self, document_id: str) -> int:
        """Count chunks for a document."""
        result = self.db.execute(
            text("SELECT COUNT(*) as count FROM knowledge_chunks WHERE document_id = :id"),
            {"id": document_id}
        )
        return result.fetchone()[0]
