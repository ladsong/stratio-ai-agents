from __future__ import annotations

from core.tools.base import BaseTool
from core.tools.implementations.artifact_writer import ArtifactWriterTool
from core.tools.implementations.document_lookup import DocumentLookupTool
from core.tools.implementations.mock_browser_research import MockBrowserResearchTool
from core.tools.implementations.postgres_query import PostgresQueryTool
from core.tools.implementations.vector_search import VectorSearchTool


def get_all_tools() -> list[BaseTool]:
    """Get all available tools."""
    return [
        PostgresQueryTool(),
        VectorSearchTool(),
        DocumentLookupTool(),
        ArtifactWriterTool(),
        MockBrowserResearchTool(),
    ]


def get_tool_by_name(name: str) -> BaseTool | None:
    """Get a tool by name."""
    tools = get_all_tools()
    for tool in tools:
        if tool.name == name:
            return tool
    return None
