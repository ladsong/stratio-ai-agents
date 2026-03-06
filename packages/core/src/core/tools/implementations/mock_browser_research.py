from __future__ import annotations

from typing import Any

from core.tools.base import BaseTool


class MockBrowserResearchTool(BaseTool):
    """Mock browser research tool (stub for future implementation)."""
    
    name = "mock_browser_research"
    description = "Perform web research (mock implementation)"
    schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Research query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5
            }
        },
        "required": ["query"]
    }
    timeout_ms = 30000
    retries = 2
    permission_tag = "network"
    
    def execute(self, query: str, max_results: int = 5) -> dict[str, Any]:
        """Execute mock browser research."""
        mock_results = [
            {
                "title": f"Result {i+1} for: {query}",
                "url": f"https://example.com/result-{i+1}",
                "snippet": f"This is a mock result snippet for query: {query}",
                "relevance_score": 0.9 - (i * 0.1)
            }
            for i in range(min(max_results, 3))
        ]
        
        return {
            "query": query,
            "results": mock_results,
            "count": len(mock_results),
            "mock": True
        }
