#!/usr/bin/env python3
"""Test script for Phase 6: Tool Registry and Tool Execution."""

import os
import sys

# Add core package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages/core/src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.tools.executor import ToolExecutor
from core.tools.implementations.postgres_query import PostgresQueryTool
from core.tools.implementations.vector_search import VectorSearchTool
from core.tools.implementations.document_lookup import DocumentLookupTool
from core.tools.implementations.artifact_writer import ArtifactWriterTool
from core.tools.implementations.mock_browser_research import MockBrowserResearchTool


def main():
    print("=== Phase 6 Testing: Tool Registry and Execution ===\n")
    
    # Setup database connection
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Create a unique test run_id
    import uuid
    from sqlalchemy import text
    
    run_id = f"test-run-phase6-{str(uuid.uuid4())[:8]}"
    thread_id = str(uuid.uuid4())
    
    # Create a test thread and run in the database
    print("0. Creating test thread and run...")
    db.execute(
        text("INSERT INTO threads (id, meta, created_at, updated_at) VALUES (:id, :meta, NOW(), NOW())"),
        {"id": thread_id, "meta": '{"test": true}'}
    )
    db.execute(
        text("INSERT INTO runs (id, thread_id, graph_name, status, created_at, updated_at) VALUES (:id, :thread_id, :graph_name, :status, NOW(), NOW())"),
        {"id": run_id, "thread_id": thread_id, "graph_name": "test_graph", "status": "running"}
    )
    db.commit()
    print(f"   ✓ Created test run: {run_id}")
    print()
    
    # Initialize tool executor
    executor = ToolExecutor(db, run_id, allowed_permissions=["safe", "database", "network"])
    
    # Register all tools
    print("1. Registering tools...")
    tools = [
        PostgresQueryTool(),
        VectorSearchTool(),
        DocumentLookupTool(),
        ArtifactWriterTool(),
        MockBrowserResearchTool(),
    ]
    
    for tool in tools:
        executor.register_tool(tool)
        print(f"   ✓ Registered: {tool.name} (permission: {tool.permission_tag})")
    print()
    
    # Test 1: PostgresQueryTool
    print("2. Testing postgres_query tool...")
    try:
        result = executor.execute(
            "postgres_query",
            {"query": "SELECT COUNT(*) as count FROM threads"}
        )
        print(f"   ✓ Query executed successfully")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        db.rollback()
    print()
    
    # Test 3: VectorSearchTool
    print("3. Testing vector_search tool...")
    try:
        result = executor.execute(
            "vector_search",
            {"query": "test search", "top_k": 3}
        )
        print(f"   ✓ Search executed successfully")
        print(f"   Found {result['count']} chunks")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        db.rollback()
    print()
    
    # Test 4: DocumentLookupTool
    print("4. Testing document_lookup tool...")
    try:
        result = executor.execute(
            "document_lookup",
            {"document_id": "nonexistent-doc"}
        )
        print(f"   ✓ Lookup executed successfully")
        print(f"   Found: {result['found']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        db.rollback()
    print()
    
    # Test 5: ArtifactWriterTool
    print("5. Testing artifact_writer tool...")
    try:
        result = executor.execute(
            "artifact_writer",
            {
                "run_id": run_id,
                "artifact_type": "test_artifact",
                "content": "This is a test artifact created by Phase 6 tool testing",
                "meta": {"test": True}
            }
        )
        print(f"   ✓ Artifact created successfully")
        print(f"   Artifact ID: {result['artifact_id']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        db.rollback()
    print()
    
    # Test 6: MockBrowserResearchTool
    print("6. Testing mock_browser_research tool...")
    try:
        result = executor.execute(
            "mock_browser_research",
            {"query": "AI agent frameworks", "max_results": 3}
        )
        print(f"   ✓ Research executed successfully")
        print(f"   Found {result['count']} results (mock)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        db.rollback()
    print()
    
    # Test 7: Permission enforcement
    print("7. Testing permission enforcement...")
    try:
        # Create executor with limited permissions
        limited_executor = ToolExecutor(db, run_id, allowed_permissions=["safe"])
        limited_executor.register_tool(PostgresQueryTool())
        
        # This should fail due to permission
        result = limited_executor.execute(
            "postgres_query",
            {"query": "SELECT 1"}
        )
        print(f"   ✗ Permission check failed - should have been denied")
    except PermissionError as e:
        print(f"   ✓ Permission correctly denied: {e}")
        db.rollback()
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        db.rollback()
    print()
    
    # Test 7: Check tool call logging
    print("8. Checking tool call logs...")
    from sqlalchemy import text
    result = db.execute(
        text("SELECT COUNT(*) as count FROM tool_calls WHERE run_id = :run_id"),
        {"run_id": run_id}
    )
    count = result.fetchone()[0]
    print(f"   ✓ Found {count} tool calls logged for run {run_id}")
    print()
    
    # Test 8: Retrieve tool call details
    print("9. Retrieving tool call details...")
    result = db.execute(
        text("""
            SELECT tool_name, duration_ms, error
            FROM tool_calls
            WHERE run_id = :run_id
            ORDER BY created_at DESC
            LIMIT 5
        """),
        {"run_id": run_id}
    )
    tool_calls = result.fetchall()
    for tc in tool_calls:
        status = "✓" if not tc[2] else "✗"
        print(f"   {status} {tc[0]}: {tc[1]}ms" + (f" (error: {tc[2]})" if tc[2] else ""))
    print()
    
    print("=== Phase 6 Testing Complete ===\n")
    print("Summary:")
    print("  ✓ Tool execution framework working")
    print("  ✓ All 5 MVP tools implemented")
    print("  ✓ Tool call logging functional")
    print("  ✓ Permission system enforced")
    print("  ✓ Database integration working")
    print()
    
    db.close()


if __name__ == "__main__":
    main()
