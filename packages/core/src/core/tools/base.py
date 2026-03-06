from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str
    description: str
    schema: dict[str, Any]
    timeout_ms: int = 5000
    retries: int = 0
    permission_tag: str = "safe"
    
    @abstractmethod
    def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool with given inputs."""
        pass
    
    def validate_inputs(self, inputs: dict[str, Any]) -> bool:
        """Validate inputs against schema."""
        return True
    
    def get_info(self) -> dict[str, Any]:
        """Get tool information for registry."""
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema,
            "timeout_ms": self.timeout_ms,
            "retries": self.retries,
            "permission_tag": self.permission_tag,
        }
