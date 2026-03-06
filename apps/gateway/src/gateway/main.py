from __future__ import annotations

import logging
import os
import sys
import uuid

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.repositories.artifact_repo import ArtifactRepository
from core.repositories.event_repo import EventRepository
from core.repositories.integration_credential_repo import IntegrationCredentialRepository
from core.repositories.knowledge_chunk_repo import KnowledgeChunkRepository
from core.repositories.knowledge_document_repo import KnowledgeDocumentRepository
from core.repositories.registry_repo import RegistryRepository
from core.repositories.run_repo import RunRepository
from core.repositories.thread_repo import ThreadRepository
from core.repositories.tool_call_repo import ToolCallRepository
from core.repositories.tool_policy_repo import ToolPolicyRepository
from gateway.dependencies import get_db, get_request_id, verify_auth
from gateway.middleware import RequestLoggingMiddleware
from gateway.queue import get_queue
from gateway.schemas import (
    ApprovalRequest,
    ArtifactResponse,
    ChunkResponse,
    DocumentCreate,
    DocumentResponse,
    EventCreate,
    EventResponse,
    GraphResponse,
    IntegrationCreate,
    IntegrationResponse,
    IntegrationRotate,
    RunCreate,
    RunResponse,
    RunStateResponse,
    ThreadCreate,
    ThreadResponse,
    ToolCallResponse,
    ToolPolicyCreate,
    ToolPolicyResponse,
    ToolResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nanobot Gateway API",
    description="REST API for nanobot agent orchestration",
    version="0.1.0",
)

cors_origins = os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    database_url = os.environ["DATABASE_URL"]
    redis_url = os.environ["REDIS_URL"]

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    r = Redis.from_url(redis_url)
    r.ping()

    return {"status": "ready"}


@app.post("/api/v1/threads", response_model=ThreadResponse, dependencies=[Depends(verify_auth)])
def create_thread(
    thread_data: ThreadCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ThreadResponse:
    thread_id = thread_data.id or str(uuid.uuid4())
    repo = ThreadRepository(db)
    thread = repo.create(thread_id, thread_data.meta)
    return ThreadResponse.model_validate(thread)


@app.get("/api/v1/threads/{thread_id}", response_model=ThreadResponse, dependencies=[Depends(verify_auth)])
def get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ThreadResponse:
    repo = ThreadRepository(db)
    thread = repo.get_by_id(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadResponse.model_validate(thread)


@app.post("/api/v1/threads/{thread_id}/events", response_model=EventResponse, dependencies=[Depends(verify_auth)])
def create_event(
    thread_id: str,
    event_data: EventCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> EventResponse:
    repo = EventRepository(db)
    
    if event_data.idempotency_key:
        existing = repo.get_by_idempotency_key(event_data.idempotency_key)
        if existing:
            return EventResponse.model_validate(existing)
    
    event_id = event_data.id or str(uuid.uuid4())
    
    try:
        event = repo.create(
            event_id=event_id,
            thread_id=thread_id,
            role=event_data.role,
            content=event_data.content,
            idempotency_key=event_data.idempotency_key,
            meta=event_data.meta,
        )
        return EventResponse.model_validate(event)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Idempotency key conflict")


@app.get("/api/v1/threads/{thread_id}/events", response_model=list[EventResponse], dependencies=[Depends(verify_auth)])
def list_events(
    thread_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[EventResponse]:
    repo = EventRepository(db)
    events = repo.list_by_thread(thread_id, limit)
    return [EventResponse.model_validate(e) for e in events]


@app.post("/api/v1/runs", response_model=RunResponse, dependencies=[Depends(verify_auth)])
def create_run(
    run_data: RunCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> RunResponse:
    run_id = run_data.id or str(uuid.uuid4())
    repo = RunRepository(db)
    run = repo.create(
        run_id=run_id,
        thread_id=run_data.thread_id,
        graph_name=run_data.graph_name,
        meta=run_data.meta,
    )
    
    queue = get_queue()
    initial_state = {
        "thread_id": run_data.thread_id,
        "run_id": run_id,
        "messages": run_data.meta.get("messages", []) if run_data.meta else []
    }
    
    queue.enqueue(
        "core.jobs.run_executor.execute_run_job",
        run_id=run_id,
        thread_id=run_data.thread_id,
        graph_name=run_data.graph_name,
        initial_state=initial_state,
        job_timeout=300,
        result_ttl=3600,
    )
    
    logger.info(f"Enqueued run {run_id} for execution")
    
    return RunResponse.model_validate(run)


@app.get("/api/v1/runs/{run_id}", response_model=RunResponse, dependencies=[Depends(verify_auth)])
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> RunResponse:
    repo = RunRepository(db)
    run = repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate(run)


@app.get("/api/v1/runs/{run_id}/state", response_model=RunStateResponse, dependencies=[Depends(verify_auth)])
def get_run_state(
    run_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> RunStateResponse:
    repo = RunRepository(db)
    run = repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunStateResponse(id=run.id, status=run.status, error=run.error)


@app.post("/api/v1/runs/{run_id}/approve", dependencies=[Depends(verify_auth)])
def approve_run(
    run_id: str,
    approval_data: ApprovalRequest,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> dict[str, str]:
    repo = RunRepository(db)
    run = repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    approval_id = str(uuid.uuid4())
    repo.create_approval(
        approval_id=approval_id,
        run_id=run_id,
        status="approved",
        response=approval_data.response,
    )
    
    queue = get_queue()
    approval_response = {
        "status": "approved",
        "approval_status": "approved",
        **approval_data.response
    }
    
    queue.enqueue(
        "core.jobs.run_executor.resume_run_job",
        run_id=run_id,
        thread_id=run.thread_id,
        graph_name=run.graph_name,
        approval_response=approval_response,
        job_timeout=300,
        result_ttl=3600,
    )
    
    logger.info(f"Enqueued resume job for run {run_id} (approved)")
    
    return {"status": "approved", "run_id": run_id}


@app.post("/api/v1/runs/{run_id}/reject", dependencies=[Depends(verify_auth)])
def reject_run(
    run_id: str,
    approval_data: ApprovalRequest,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> dict[str, str]:
    repo = RunRepository(db)
    run = repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    approval_id = str(uuid.uuid4())
    repo.create_approval(
        approval_id=approval_id,
        run_id=run_id,
        status="rejected",
        response=approval_data.response,
    )
    
    repo.update_status(run_id, "failed", error="Rejected by user")
    
    logger.info(f"Run {run_id} rejected by user")
    
    return {"status": "rejected", "run_id": run_id}


@app.post("/api/v1/runs/{run_id}/resume", dependencies=[Depends(verify_auth)])
def resume_run(
    run_id: str,
    approval_data: ApprovalRequest,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> dict[str, str]:
    repo = RunRepository(db)
    run = repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    repo.update_status(run_id, "running")
    
    return {"status": "resumed", "run_id": run_id}


@app.get("/api/v1/artifacts/{artifact_id}", response_model=ArtifactResponse, dependencies=[Depends(verify_auth)])
def get_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ArtifactResponse:
    repo = ArtifactRepository(db)
    artifact = repo.get_by_id(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactResponse.model_validate(artifact)


@app.get("/api/v1/tools", response_model=list[ToolResponse], dependencies=[Depends(verify_auth)])
def list_tools(
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[ToolResponse]:
    repo = RegistryRepository(db)
    tools = repo.list_tools()
    return [ToolResponse.model_validate(t) for t in tools]


@app.get("/api/v1/graphs", response_model=list[GraphResponse], dependencies=[Depends(verify_auth)])
def list_graphs(
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[GraphResponse]:
    repo = RegistryRepository(db)
    graphs = repo.list_graphs()
    return [GraphResponse.model_validate(g) for g in graphs]


@app.get("/api/v1/runs/{run_id}/tool-calls", response_model=list[ToolCallResponse], dependencies=[Depends(verify_auth)])
def list_run_tool_calls(
    run_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[ToolCallResponse]:
    repo = ToolCallRepository(db)
    tool_calls = repo.list_by_run(run_id, limit)
    return [ToolCallResponse.model_validate(tc) for tc in tool_calls]


@app.get("/api/v1/tool-calls/{tool_call_id}", response_model=ToolCallResponse, dependencies=[Depends(verify_auth)])
def get_tool_call(
    tool_call_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ToolCallResponse:
    repo = ToolCallRepository(db)
    tool_call = repo.get_by_id(tool_call_id)
    if not tool_call:
        raise HTTPException(status_code=404, detail="Tool call not found")
    return ToolCallResponse.model_validate(tool_call)


@app.post("/api/v1/knowledge/documents", response_model=DocumentResponse, dependencies=[Depends(verify_auth)])
def create_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> DocumentResponse:
    document_id = str(uuid.uuid4())
    repo = KnowledgeDocumentRepository(db)
    
    document = repo.create(
        document_id=document_id,
        title=document_data.title,
        content=document_data.content,
        meta=document_data.meta
    )
    
    queue = get_queue()
    queue.enqueue(
        "core.jobs.chunk_document.chunk_document_job",
        document_id=document_id,
        generate_embeddings=True,
        job_timeout=300,
        result_ttl=3600,
    )
    
    logger.info(f"Enqueued chunking job for document {document_id}")
    
    chunk_count = repo.count_chunks(document_id)
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        meta=document.meta,
        chunk_count=chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at
    )


@app.get("/api/v1/knowledge/documents", response_model=list[DocumentResponse], dependencies=[Depends(verify_auth)])
def list_documents(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[DocumentResponse]:
    repo = KnowledgeDocumentRepository(db)
    documents = repo.list_documents(limit, offset)
    
    responses = []
    for doc in documents:
        chunk_count = repo.count_chunks(doc.id)
        responses.append(DocumentResponse(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            meta=doc.meta,
            chunk_count=chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        ))
    
    return responses


@app.get("/api/v1/knowledge/documents/{document_id}", response_model=DocumentResponse, dependencies=[Depends(verify_auth)])
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> DocumentResponse:
    repo = KnowledgeDocumentRepository(db)
    document = repo.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunk_count = repo.count_chunks(document_id)
    
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        meta=document.meta,
        chunk_count=chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at
    )


@app.get("/api/v1/knowledge/documents/{document_id}/chunks", response_model=list[ChunkResponse], dependencies=[Depends(verify_auth)])
def get_document_chunks(
    document_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[ChunkResponse]:
    chunk_repo = KnowledgeChunkRepository(db)
    chunks = chunk_repo.list_by_document(document_id, limit)
    
    return [ChunkResponse(
        id=chunk.id,
        document_id=chunk.document_id,
        content=chunk.content,
        has_embedding=chunk.has_embedding,
        meta=chunk.meta,
        created_at=chunk.created_at,
        updated_at=chunk.updated_at
    ) for chunk in chunks]


# Integration Credentials Endpoints

@app.get("/api/v1/config/integrations", response_model=list[IntegrationResponse])
async def list_integrations(
    integration_type: Optional[str] = None,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> list[IntegrationResponse]:
    repo = IntegrationCredentialRepository(db)
    credentials = repo.list_by_type(integration_type)
    
    return [IntegrationResponse(
        id=cred.id,
        integration_type=cred.integration_type,
        display_name=cred.display_name,
        status=cred.status,
        meta=cred.meta,
        created_at=cred.created_at,
        updated_at=cred.updated_at
    ) for cred in credentials]


@app.post("/api/v1/config/integrations/{integration_type}", response_model=IntegrationResponse)
async def create_integration(
    integration_type: str,
    data: IntegrationCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> IntegrationResponse:
    import uuid
    
    repo = IntegrationCredentialRepository(db)
    credential = repo.create(
        credential_id=str(uuid.uuid4()),
        integration_type=integration_type,
        display_name=data.display_name,
        token=data.token,
        meta=data.meta
    )
    
    return IntegrationResponse(
        id=credential.id,
        integration_type=credential.integration_type,
        display_name=credential.display_name,
        status=credential.status,
        meta=credential.meta,
        created_at=credential.created_at,
        updated_at=credential.updated_at
    )


@app.post("/api/v1/config/integrations/{credential_id}/rotate", response_model=IntegrationResponse)
async def rotate_integration(
    credential_id: str,
    data: IntegrationRotate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> IntegrationResponse:
    repo = IntegrationCredentialRepository(db)
    credential = repo.update_token(credential_id, data.token)
    
    if not credential:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return IntegrationResponse(
        id=credential.id,
        integration_type=credential.integration_type,
        display_name=credential.display_name,
        status=credential.status,
        meta=credential.meta,
        created_at=credential.created_at,
        updated_at=credential.updated_at
    )


@app.delete("/api/v1/config/integrations/{credential_id}")
async def delete_integration(
    credential_id: str,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    repo = IntegrationCredentialRepository(db)
    deleted = repo.delete(credential_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return {"status": "deleted", "id": credential_id}


# Tool Policy Endpoints

@app.get("/api/v1/config/tool-policy", response_model=ToolPolicyResponse)
async def get_tool_policy(
    scope_type: str,
    scope_id: Optional[str] = None,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ToolPolicyResponse:
    repo = ToolPolicyRepository(db)
    policy = repo.get_policy(scope_type, scope_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return ToolPolicyResponse(
        id=policy.id,
        scope_type=policy.scope_type,
        scope_id=policy.scope_id,
        mode=policy.mode,
        tools=policy.tools.get("tools", []),
        created_at=policy.created_at,
        updated_at=policy.updated_at
    )


@app.put("/api/v1/config/tool-policy", response_model=ToolPolicyResponse)
async def update_tool_policy(
    data: ToolPolicyCreate,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
) -> ToolPolicyResponse:
    import uuid
    
    repo = ToolPolicyRepository(db)
    policy = repo.create_or_update(
        policy_id=str(uuid.uuid4()),
        scope_type=data.scope_type,
        scope_id=data.scope_id,
        mode=data.mode,
        tools=data.tools
    )
    
    return ToolPolicyResponse(
        id=policy.id,
        scope_type=policy.scope_type,
        scope_id=policy.scope_id,
        mode=policy.mode,
        tools=policy.tools.get("tools", []),
        created_at=policy.created_at,
        updated_at=policy.updated_at
    )


@app.delete("/api/v1/config/tool-policy")
async def delete_tool_policy(
    scope_type: str,
    scope_id: Optional[str] = None,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id),
):
    repo = ToolPolicyRepository(db)
    deleted = repo.delete(scope_type, scope_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {"status": "deleted", "scope_type": scope_type, "scope_id": scope_id}
