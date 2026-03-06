"""Wrapper for nanobot tools to work with backend ToolExecutor."""

from typing import Any
import asyncio


class NanobotToolWrapper:
    """Wraps a nanobot tool for use in backend."""
    
    def __init__(self, nanobot_tool):
        self._tool = nanobot_tool
    
    @property
    def name(self) -> str:
        return self._tool.name
    
    @property
    def description(self) -> str:
        return self._tool.description
    
    @property
    def schema(self) -> dict[str, Any]:
        """Get tool schema."""
        return self._tool.parameters or {}
    
    @property
    def permission_tag(self) -> str:
        """Map nanobot tools to permission levels."""
        dangerous_tools = ["exec", "write_file", "spawn"]
        network_tools = ["web_search", "fetch_url"]
        
        if self._tool.name in dangerous_tools:
            return "admin"
        elif self._tool.name in network_tools:
            return "network"
        else:
            return "safe"
    
    @property
    def timeout_ms(self) -> int:
        """Get timeout in milliseconds."""
        return 30000  # 30 seconds default
    
    @property
    def retries(self) -> int:
        """Get retry count."""
        return 2
    
    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """Validate inputs using nanobot's validation."""
        errors = self._tool.validate_params(inputs)
        return len(errors) == 0
    
    async def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute the nanobot tool."""
        try:
            result = await self._tool.execute(**inputs)
            return {
                "output": result,
                "tool": self._tool.name,
                "success": True
            }
        except Exception as e:
            return {
                "output": str(e),
                "tool": self._tool.name,
                "success": False,
                "error": str(e)
            }


def load_nanobot_tools() -> list[NanobotToolWrapper]:
    """Load all nanobot tools."""
    try:
        from nanobot.agent.tools.shell import ExecTool
        from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool
        from nanobot.agent.tools.web import WebSearchTool, FetchUrlTool
        from nanobot.agent.tools.message import MessageTool
        
        tools = [
            ExecTool(),
            ReadFileTool(),
            WriteFileTool(),
            ListDirTool(),
            WebSearchTool(),
            FetchUrlTool(),
            MessageTool(),
        ]
        
        return [NanobotToolWrapper(tool) for tool in tools]
    except ImportError as e:
        # Nanobot not installed yet, return empty list
        return []
