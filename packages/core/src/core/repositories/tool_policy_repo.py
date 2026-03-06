"""Repository for managing tool policies."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from core.db.models import ToolPolicy


class ToolPolicyRepository:
    """Repository for tool policy operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_update(
        self,
        policy_id: str,
        scope_type: str,
        scope_id: str | None,
        mode: str,
        tools: list[str]
    ) -> ToolPolicy:
        """
        Create or update a tool policy.
        
        Args:
            policy_id: Unique policy ID
            scope_type: Scope type (global, workspace, thread)
            scope_id: Scope ID (None for global)
            mode: Policy mode (allowlist, denylist)
            tools: List of tool names
            
        Returns:
            Created or updated ToolPolicy
        """
        # Check if policy exists for this scope
        existing = self.get_policy(scope_type, scope_id)
        
        if existing:
            # Update existing policy
            existing.mode = mode
            existing.tools = {"tools": tools}
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new policy
        policy = ToolPolicy(
            id=policy_id,
            scope_type=scope_type,
            scope_id=scope_id,
            mode=mode,
            tools={"tools": tools}
        )
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    def get_policy(self, scope_type: str, scope_id: str | None = None) -> ToolPolicy | None:
        """
        Get policy for a specific scope.
        
        Args:
            scope_type: Scope type (global, workspace, thread)
            scope_id: Scope ID (None for global)
            
        Returns:
            ToolPolicy or None
        """
        query = select(ToolPolicy).where(
            and_(
                ToolPolicy.scope_type == scope_type,
                ToolPolicy.scope_id == scope_id
            )
        )
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_effective_policy(
        self,
        thread_id: str | None = None,
        workspace_id: str | None = None
    ) -> ToolPolicy | None:
        """
        Get effective policy using hierarchy: thread → workspace → global.
        
        Args:
            thread_id: Thread ID
            workspace_id: Workspace ID
            
        Returns:
            Most specific ToolPolicy or None
        """
        # Try thread-level policy first
        if thread_id:
            thread_policy = self.get_policy("thread", thread_id)
            if thread_policy:
                return thread_policy
        
        # Try workspace-level policy
        if workspace_id:
            workspace_policy = self.get_policy("workspace", workspace_id)
            if workspace_policy:
                return workspace_policy
        
        # Fall back to global policy
        global_policy = self.get_policy("global", None)
        return global_policy
    
    def list_policies(self, scope_type: str | None = None) -> list[ToolPolicy]:
        """
        List all policies, optionally filtered by scope type.
        
        Args:
            scope_type: Optional filter by scope type
            
        Returns:
            List of ToolPolicy
        """
        query = select(ToolPolicy)
        
        if scope_type:
            query = query.where(ToolPolicy.scope_type == scope_type)
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def delete(self, scope_type: str, scope_id: str | None = None) -> bool:
        """
        Delete a policy.
        
        Args:
            scope_type: Scope type
            scope_id: Scope ID
            
        Returns:
            True if deleted, False if not found
        """
        policy = self.get_policy(scope_type, scope_id)
        if not policy:
            return False
        
        self.db.delete(policy)
        self.db.commit()
        
        return True
    
    def get_allowed_tools(
        self,
        thread_id: str | None = None,
        workspace_id: str | None = None
    ) -> set[str]:
        """
        Get set of allowed tools for a context.
        
        Args:
            thread_id: Thread ID
            workspace_id: Workspace ID
            
        Returns:
            Set of allowed tool names
        """
        policy = self.get_effective_policy(thread_id, workspace_id)
        
        if not policy:
            # No policy = deny all (secure by default)
            return set()
        
        tools_list = policy.tools.get("tools", [])
        
        if policy.mode == "allowlist":
            return set(tools_list)
        else:
            # For denylist, we'd need all available tools
            # This is a simplified version - return empty for now
            # In production, you'd get all registered tools and subtract denied ones
            return set()
