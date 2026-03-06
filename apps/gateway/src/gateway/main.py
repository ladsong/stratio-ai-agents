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
from core.repositories.registry_repo import RegistryRepository
from core.repositories.run_repo import RunRepository
from core.repositories.thread_repo import ThreadRepository
from core.repositories.tool_call_repo import ToolCallRepository
from gateway.dependencies import get_db, get_request_id, verify_auth
from gateway.middleware import RequestLoggingMiddleware
from gateway.queue import get_queue
from gateway.schemas import (
    ApprovalRequest,
    ArtifactResponse,
    EventCreate,
    EventResponse,
    GraphResponse,
    RunCreate,
    RunResponse,
    RunStateResponse,
    ThreadCreate,
    ThreadResponse,
    ToolCallResponse,
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
