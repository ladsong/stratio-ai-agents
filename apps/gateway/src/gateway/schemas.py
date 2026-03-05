from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ThreadCreate(BaseModel):
    id: Optional[str] = None
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
