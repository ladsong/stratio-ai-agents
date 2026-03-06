from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from core.repositories.tool_policy_repo import ToolPolicyRepository
from core.tools.base import BaseTool
from core.tools.logger import ToolCallLogger


logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executor for running tools with permission checking and logging."""
    
    PERMISSION_LEVELS = ["safe", "database", "network", "admin"]
    
    def __init__(
        self, 
        db: Session, 
        run_id: str,
        thread_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        allowed_permissions: list[str] | None = None
    ):
        self.db = db
        self.run_id = run_id
        self.thread_id = thread_id
        self.workspace_id = workspace_id
        self.allowed_permissions = allowed_permissions or ["safe", "database", "network"]
        self.tools: dict[str, BaseTool] = {}
        
        # Load tool policy
        self.policy_repo = ToolPolicyRepository(db)
        self.allowed_tools = self._load_allowed_tools()
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool for execution."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def _load_allowed_tools(self) -> set[str]:
        """Load allowed tools from policy hierarchy."""
        try:
            return self.policy_repo.get_allowed_tools(self.thread_id, self.workspace_id)
        except Exception as e:
            logger.warning(f"Failed to load tool policy, defaulting to empty allowlist: {e}")
            return set()
    
    def check_permission(self, tool: BaseTool) -> bool:
        """Check if tool has required permission."""
        return tool.permission_tag in self.allowed_permissions
    
    def check_tool_policy(self, tool_name: str) -> bool:
        """Check if tool is allowed by policy."""
        # If no policy is set, deny all (secure by default)
        if not self.allowed_tools:
            return False
        return tool_name in self.allowed_tools
    
    def execute(self, tool_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with policy and permission checking."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Check tool policy first
        if not self.check_tool_policy(tool_name):
            error_msg = f"Tool denied by policy: {tool_name}"
            logger.error(
                error_msg,
                extra={
                    "run_id": self.run_id,
                    "tool_name": tool_name,
                    "reason": "denied_by_policy",
                    "thread_id": self.thread_id,
                    "workspace_id": self.workspace_id
                }
            )
            raise PermissionError(error_msg)
        
        # Check permission level
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
