from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ThreadCreate(BaseModel):
    id: Optional[str] = None
    meta: Optional[dict] = None


class ThreadUpdate(BaseModel):
    system_prompt: Optional[str] = None
    meta: Optional[dict] = None


class ThreadResponse(BaseModel):
    id: str
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    id: Optional[str] = None
    role: str
    content: Optional[str] = None
    idempotency_key: Optional[str] = None
    meta: Optional[dict] = None


class EventResponse(BaseModel):
    id: str
    thread_id: str
    role: str
    content: Optional[str] = None
    idempotency_key: Optional[str] = None
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunCreate(BaseModel):
    id: Optional[str] = None
    thread_id: str
    graph_name: str
    meta: Optional[dict] = None


class RunResponse(BaseModel):
    id: str
    thread_id: str
    graph_name: str
    status: str
    error: Optional[str] = None
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunStateResponse(BaseModel):
    id: str
    status: str
    error: Optional[str] = None


class ApprovalRequest(BaseModel):
    response: Optional[dict] = None


class ArtifactResponse(BaseModel):
    id: str
    run_id: str
    artifact_type: str
    content: Optional[str] = None
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    schema: Optional[dict] = None
    timeout_ms: Optional[int] = None
    retries: Optional[int] = None
    permission_tag: Optional[str] = None

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    config: Optional[dict] = None

    class Config:
        from_attributes = True


class ToolCallResponse(BaseModel):
    id: str
    run_id: str
    tool_name: str
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    title: Optional[str] = None
    content: str
    meta: Optional[dict] = None


class DocumentResponse(BaseModel):
    id: str
    title: Optional[str] = None
    content: str
    meta: Optional[dict] = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    content: str
    has_embedding: bool = False
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntegrationCreate(BaseModel):
    display_name: str
    token: str
    meta: Optional[dict] = None


class IntegrationResponse(BaseModel):
    id: str
    integration_type: str
    display_name: str
    status: str
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntegrationRotate(BaseModel):
    token: str


class ToolPolicyCreate(BaseModel):
    scope_type: str
    scope_id: Optional[str] = None
    mode: str = "allowlist"
    tools: list[str]


class ToolPolicyResponse(BaseModel):
    id: str
    scope_type: str
    scope_id: Optional[str] = None
    mode: str
    tools: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMProviderCreate(BaseModel):
    provider: str
    display_name: str
    api_key: str
    model: str
    api_base: Optional[str] = None
    extra_headers: Optional[dict] = None
    is_default: bool = False


class LLMProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    api_base: Optional[str] = None
    extra_headers: Optional[dict] = None
    is_default: Optional[bool] = None


class LLMProviderResponse(BaseModel):
    id: str
    provider: str
    display_name: str
    model: str
    api_base: Optional[str] = None
    is_default: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserContactResponse(BaseModel):
    id: str
    channel: str
    contact_id: str
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    role: str = "user"
    system_prompt: Optional[str] = None
    meta: Optional[dict] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    meta: Optional[dict] = None


class UserResponse(BaseModel):
    id: str
    name: str
    role: str
    system_prompt: Optional[str] = None
    meta: Optional[dict] = None
    contacts: list[UserContactResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserContactCreate(BaseModel):
    channel: str
    contact_id: str
    meta: Optional[dict] = None
