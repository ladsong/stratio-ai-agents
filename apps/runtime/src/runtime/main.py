from __future__ import annotations

import logging
import sys
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from runtime.executor import GraphExecutor
from runtime.graphs.registry import list_available_graphs


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nanobot Runtime API",
    description="LangGraph workflow execution service",
    version="0.1.0",
)

executor = GraphExecutor()


class ExecuteRequest(BaseModel):
    run_id: str
    thread_id: str
    graph_name: str
    initial_state: dict[str, Any]
    config: dict[str, Any] | None = None


class ResumeRequest(BaseModel):
    run_id: str
    thread_id: str
    graph_name: str
    approval_response: dict[str, Any]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/graphs")
def list_graphs() -> dict[str, list[str]]:
    return {"graphs": list_available_graphs()}


@app.post("/execute")
def execute_graph(request: ExecuteRequest) -> dict[str, Any]:
    try:
        logger.info(f"Executing graph {request.graph_name} for run {request.run_id}")
        
        result = executor.execute_graph(
            run_id=request.run_id,
            thread_id=request.thread_id,
            graph_name=request.graph_name,
            initial_state=request.initial_state,
            config=request.config
        )
        
        logger.info(f"Graph execution result: {result.get('status')}")
        return result
    
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resume")
def resume_graph(request: ResumeRequest) -> dict[str, Any]:
    try:
        logger.info(f"Resuming graph {request.graph_name} for run {request.run_id}")
        
        result = executor.resume_graph(
            run_id=request.run_id,
            thread_id=request.thread_id,
            graph_name=request.graph_name,
            approval_response=request.approval_response
        )
        
        logger.info(f"Graph resume result: {result.get('status')}")
        return result
    
    except Exception as e:
        logger.error(f"Graph resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
