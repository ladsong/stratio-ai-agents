from __future__ import annotations

import logging
import os
from typing import Any

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)


def get_db_session():
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def execute_run_job(run_id: str, thread_id: str, graph_name: str, initial_state: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a run by calling the runtime service.
    This function is executed by the RQ worker.
    """
    logger.info(f"Starting job execution for run {run_id}")
    
    db = get_db_session()
    runtime_url = os.environ.get("RUNTIME_URL", "http://localhost:8010")
    
    try:
        db.execute(
            text("UPDATE runs SET status = :status WHERE id = :run_id"),
            {"status": "running", "run_id": run_id}
        )
        db.commit()
        logger.info(f"Updated run {run_id} status to running")
        
        response = requests.post(
            f"{runtime_url}/execute",
            json={
                "run_id": run_id,
                "thread_id": thread_id,
                "graph_name": graph_name,
                "initial_state": initial_state
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Runtime execution completed for run {run_id}: {result.get('status')}")
        
        return {
            "run_id": run_id,
            "status": result.get("status"),
            "result": result
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Runtime service error for run {run_id}: {e}")
        db.execute(
            text("UPDATE runs SET status = :status, error = :error WHERE id = :run_id"),
            {"status": "failed", "error": f"Runtime service error: {str(e)}", "run_id": run_id}
        )
        db.commit()
        raise
    
    except Exception as e:
        logger.error(f"Job execution failed for run {run_id}: {e}")
        db.execute(
            text("UPDATE runs SET status = :status, error = :error WHERE id = :run_id"),
            {"status": "failed", "error": str(e), "run_id": run_id}
        )
        db.commit()
        raise
    
    finally:
        db.close()


def resume_run_job(run_id: str, thread_id: str, graph_name: str, approval_response: dict[str, Any]) -> dict[str, Any]:
    """
    Resume a run after approval by calling the runtime service.
    This function is executed by the RQ worker.
    """
    logger.info(f"Starting resume job for run {run_id}")
    
    db = get_db_session()
    runtime_url = os.environ.get("RUNTIME_URL", "http://localhost:8010")
    
    try:
        db.execute(
            text("UPDATE runs SET status = :status WHERE id = :run_id"),
            {"status": "running", "run_id": run_id}
        )
        db.commit()
        logger.info(f"Updated run {run_id} status to running (resume)")
        
        response = requests.post(
            f"{runtime_url}/resume",
            json={
                "run_id": run_id,
                "thread_id": thread_id,
                "graph_name": graph_name,
                "approval_response": approval_response
            },
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Runtime resume completed for run {run_id}: {result.get('status')}")
        
        return {
            "run_id": run_id,
            "status": result.get("status"),
            "result": result
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Runtime service error for run {run_id} (resume): {e}")
        db.execute(
            text("UPDATE runs SET status = :status, error = :error WHERE id = :run_id"),
            {"status": "failed", "error": f"Runtime service error: {str(e)}", "run_id": run_id}
        )
        db.commit()
        raise
    
    except Exception as e:
        logger.error(f"Resume job failed for run {run_id}: {e}")
        db.execute(
            text("UPDATE runs SET status = :status, error = :error WHERE id = :run_id"),
            {"status": "failed", "error": str(e), "run_id": run_id}
        )
        db.commit()
        raise
    
    finally:
        db.close()
