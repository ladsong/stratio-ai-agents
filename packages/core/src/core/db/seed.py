from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import text

from core.db.engine import SessionLocal
from core.db.models import Thread, GraphRegistry, ToolRegistry


def seed_database() -> None:
    db = SessionLocal()
    try:
        thread_id = str(uuid.uuid4())
        thread = Thread(
            id=thread_id,
            meta={"source": "seed", "description": "Initial test thread"}
        )
        db.add(thread)

        graphs = [
            GraphRegistry(
                id=str(uuid.uuid4()),
                name="default",
                description="Default graph for basic agent execution",
                config={"max_iterations": 40, "timeout_ms": 300000}
            ),
            GraphRegistry(
                id=str(uuid.uuid4()),
                name="conversation_router",
                description="Routes conversations to appropriate strategy graphs",
                config={"timeout_ms": 60000}
            ),
            GraphRegistry(
                id=str(uuid.uuid4()),
                name="strategy_synthesis",
                description="Synthesizes strategic artifacts with approval flow",
                config={"timeout_ms": 120000, "requires_approval": True}
            ),
        ]
        db.add_all(graphs)

        tools = [
            ToolRegistry(
                id=str(uuid.uuid4()),
                name="postgres_query",
                description="Execute read-only SQL queries to retrieve data from the database",
                schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                timeout_ms=10000,
                retries=1,
                permission_tag="database"
            ),
            ToolRegistry(
                id=str(uuid.uuid4()),
                name="vector_search",
                description="Search knowledge base using semantic similarity",
                schema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}}, "required": ["query"]},
                timeout_ms=5000,
                retries=1,
                permission_tag="database"
            ),
            ToolRegistry(
                id=str(uuid.uuid4()),
                name="document_lookup",
                description="Retrieve a specific document by its ID",
                schema={"type": "object", "properties": {"document_id": {"type": "string"}}, "required": ["document_id"]},
                timeout_ms=2000,
                retries=1,
                permission_tag="safe"
            ),
            ToolRegistry(
                id=str(uuid.uuid4()),
                name="artifact_writer",
                description="Create an artifact record linked to a run",
                schema={"type": "object", "properties": {"run_id": {"type": "string"}, "artifact_type": {"type": "string"}, "content": {"type": "string"}, "meta": {"type": "object"}}, "required": ["run_id", "artifact_type", "content"]},
                timeout_ms=5000,
                retries=1,
                permission_tag="safe"
            ),
            ToolRegistry(
                id=str(uuid.uuid4()),
                name="mock_browser_research",
                description="Perform web research (mock implementation)",
                schema={"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "default": 5}}, "required": ["query"]},
                timeout_ms=30000,
                retries=2,
                permission_tag="network"
            ),
        ]
        db.add_all(tools)

        db.commit()
        print(f"✓ Seeded database with thread {thread_id}, 1 graph, and {len(tools)} tools")
    except Exception as e:
        db.rollback()
        print(f"✗ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
