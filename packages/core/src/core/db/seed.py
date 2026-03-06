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
                name="echo",
                description="Echo back the input",
                schema={"type": "object", "properties": {"message": {"type": "string"}}},
                timeout_ms=5000,
                retries=3,
                permission_tag="safe"
            ),
            ToolRegistry(
                id=str(uuid.uuid4()),
                name="web_search",
                description="Search the web for information",
                schema={"type": "object", "properties": {"query": {"type": "string"}}},
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
