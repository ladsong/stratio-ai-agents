from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text

from core.tools.base import BaseTool


class PostgresQueryTool(BaseTool):
    """Execute read-only SQL queries against the database."""
    
    name = "postgres_query"
    description = "Execute read-only SQL queries to retrieve data from the database"
    schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL query to execute (SELECT only)"
            }
        },
        "required": ["query"]
    }
    timeout_ms = 10000
    retries = 1
    permission_tag = "database"
    
    def execute(self, query: str) -> dict[str, Any]:
        """Execute a read-only SQL query."""
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        
        if any(keyword in query_upper for keyword in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]):
            raise ValueError("Only read-only queries are allowed")
        
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
        )
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]
        
        return {
            "rows": rows,
            "count": len(rows)
        }
