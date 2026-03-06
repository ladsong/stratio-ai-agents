"""Tool policy management API endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.repositories.tool_policy_repo import ToolPolicyRepository
from gateway.dependencies import get_db, get_request_id, verify_auth
from gateway.schemas import ToolPolicyCreate, ToolPolicyResponse

router = APIRouter(prefix="/api/v1/tool-policies", tags=["tool-policies"])


class ToolPolicyUpdate(BaseModel):
    mode: Optional[str] = None
    tools: Optional[list[str]] = None


@router.get("", response_model=list[ToolPolicyResponse], dependencies=[Depends(verify_auth)])
def list_tool_policies(
    scope_type: Optional[str] = None,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[ToolPolicyResponse]:
    """List all tool policies, optionally filtered by scope type."""
    repo = ToolPolicyRepository(db)
    policies = repo.list_policies(scope_type=scope_type)
    return [ToolPolicyResponse.model_validate(p) for p in policies]


@router.post("", response_model=ToolPolicyResponse, dependencies=[Depends(verify_auth)])
def create_tool_policy(
    policy_data: ToolPolicyCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ToolPolicyResponse:
    """Create a new tool policy."""
    policy_id = str(uuid.uuid4())
    repo = ToolPolicyRepository(db)
    
    policy = repo.create_or_update(
        policy_id=policy_id,
        scope_type=policy_data.scope_type,
        scope_id=policy_data.scope_id,
        mode=policy_data.mode,
        tools=policy_data.tools
    )
    
    return ToolPolicyResponse.model_validate(policy)


@router.delete("/{scope_type}/{scope_id}", dependencies=[Depends(verify_auth)])
def delete_tool_policy(
    scope_type: str,
    scope_id: Optional[str] = None,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> dict[str, str]:
    """Delete a tool policy by scope."""
    repo = ToolPolicyRepository(db)
    
    deleted = repo.delete(scope_type, scope_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool policy not found")
    
    return {"status": "deleted", "scope_type": scope_type, "scope_id": scope_id or "global"}
