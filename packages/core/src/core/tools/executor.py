from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from core.tools.base import BaseTool
from core.tools.logger import ToolCallLogger


logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executor for running tools with permission checking and logging."""
    
    PERMISSION_LEVELS = ["safe", "database", "network", "admin"]
    
    def __init__(self, db: Session, run_id: str, allowed_permissions: list[str] | None = None):
        self.db = db
        self.run_id = run_id
        self.allowed_permissions = allowed_permissions or ["safe", "database", "network"]
        self.tools: dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool for execution."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def check_permission(self, tool: BaseTool) -> bool:
        """Check if tool has required permission."""
        return tool.permission_tag in self.allowed_permissions
    
    def execute(self, tool_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with logging and permission checking."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        if not self.check_permission(tool):
            error_msg = f"Permission denied: {tool_name} requires {tool.permission_tag}"
            logger.error(error_msg)
            raise PermissionError(error_msg)
        
        tool_logger = ToolCallLogger(self.db, self.run_id)
        tool_call_id = tool_logger.start(tool_name, inputs)
        
        try:
            if not tool.validate_inputs(inputs):
                raise ValueError(f"Invalid inputs for tool: {tool_name}")
            
            logger.info(f"Executing tool {tool_name} (call_id={tool_call_id})")
            outputs = tool.execute(**inputs)
            
            tool_logger.complete(outputs)
            
            return outputs
        
        except Exception as e:
            error_msg = str(e)
            tool_logger.fail(error_msg)
            raise
