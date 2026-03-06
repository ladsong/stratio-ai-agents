from __future__ import annotations

import json
import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.db.models import Thread, User
from runtime.checkpoints import get_checkpoint_saver
from runtime.graphs.registry import get_graph


def get_db_session():
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://nanobot:nanobot@localhost:5432/nanobot"
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


class GraphExecutor:
    def __init__(self):
        self.checkpoint_saver = get_checkpoint_saver()
        self.checkpointer_config = {"checkpointer": self.checkpoint_saver}
        
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@postgres:5432/nanobot"
        )
        self.engine = create_engine(database_url, pool_pre_ping=True)
    
    def execute_graph(
        self,
        run_id: str,
        thread_id: str,
        graph_name: str,
        initial_state: dict[str, Any],
        config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        Session = sessionmaker(bind=self.engine)
        db = Session()
        
        try:
            db.execute(
                text("UPDATE runs SET status = :status WHERE id = :run_id"),
                {"status": "running", "run_id": run_id}
            )
            db.commit()
            
            # Load thread to get user context
            thread = db.query(Thread).filter(Thread.id == thread_id).first()
            
            # Get user_id and user_role from run meta or thread
            user_id = initial_state.get("user_id")
            user_role = initial_state.get("user_role")
            
            if not user_id and thread and thread.user_id:
                user_id = thread.user_id
            
            # Load user to get system_prompt and role
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    initial_state["user_id"] = user_id
                    initial_state["user_role"] = user.role
                    if user.system_prompt:
                        initial_state["system_prompt"] = user.system_prompt
            elif user_role:
                # User role passed but no user_id, just use the role
                initial_state["user_role"] = user_role
            
            # Fallback: check thread meta for system_prompt
            if "system_prompt" not in initial_state and thread and thread.meta:
                system_prompt = thread.meta.get("system_prompt")
                if system_prompt:
                    initial_state["system_prompt"] = system_prompt
            
            graph_config_dict = config or {}
            graph_config_dict["checkpointer"] = self.checkpoint_saver
            
            graph = get_graph(graph_name, graph_config_dict)
            
            graph_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": graph_name,
                }
            }
            
            result = None
            interrupted = False
            
            try:
                for event in graph.stream(initial_state, graph_config):
                    result = event
                    
            except Exception as e:
                if "interrupt" in str(e).lower():
                    interrupted = True
                    db.execute(
                        text("UPDATE runs SET status = :status WHERE id = :run_id"),
                        {"status": "waiting_approval", "run_id": run_id}
                    )
                    db.commit()
                    
                    return {
                        "status": "waiting_approval",
                        "run_id": run_id,
                        "interrupted": True,
                        "checkpoint_saved": True
                    }
                else:
                    raise
            
            if not interrupted:
                # LangGraph stream returns {node_name: state_dict}
                # Extract the actual state from the last node
                if result and isinstance(result, dict):
                    final_state = list(result.values())[0] if result else initial_state
                else:
                    final_state = result if result else initial_state
                
                artifact_id = final_state.get("artifact_id")
                if artifact_id:
                    artifact_content = final_state.get("artifact_content", {})
                    
                    db.execute(
                        text("""
                            INSERT INTO artifacts (id, run_id, artifact_type, content, meta)
                            VALUES (:id, :run_id, :artifact_type, :content, :meta)
                        """),
                        {
                            "id": artifact_id,
                            "run_id": run_id,
                            "artifact_type": "strategy_document",
                            "content": str(artifact_content),
                            "meta": json.dumps({})
                        }
                    )
                
                db.execute(
                    text("UPDATE runs SET status = :status WHERE id = :run_id"),
                    {"status": "completed", "run_id": run_id}
                )
                db.commit()
                
                return {
                    "status": "completed",
                    "run_id": run_id,
                    "result": final_state,
                    "artifact_id": artifact_id
                }
        
        except Exception as e:
            db.execute(
                text("UPDATE runs SET status = :status, error = :error WHERE id = :run_id"),
                {"status": "failed", "error": str(e), "run_id": run_id}
            )
            db.commit()
            raise
        
        finally:
            db.close()
    
    def resume_graph(
        self,
        run_id: str,
        thread_id: str,
        graph_name: str,
        approval_response: dict[str, Any]
    ) -> dict[str, Any]:
        Session = sessionmaker(bind=self.engine)
        db = Session()
        
        try:
            db.execute(
                text("UPDATE runs SET status = :status WHERE id = :run_id"),
                {"status": "running", "run_id": run_id}
            )
            db.commit()
            
            # Load thread to get user context
            thread = db.query(Thread).filter(Thread.id == thread_id).first()
            
            # Load user to get system_prompt and role
            user_id = None
            user_role = None
            system_prompt = None
            
            if thread and thread.user_id:
                user = db.query(User).filter(User.id == thread.user_id).first()
                if user:
                    user_id = user.id
                    user_role = user.role
                    system_prompt = user.system_prompt
            
            # Fallback: check thread meta
            if not system_prompt and thread and thread.meta:
                system_prompt = thread.meta.get("system_prompt")
            
            graph_config_dict = {"checkpointer": self.checkpoint_saver}
            graph = get_graph(graph_name, graph_config_dict)
            
            graph_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": graph_name,
                }
            }
            
            result = None
            
            for event in graph.stream(approval_response, graph_config):
                result = event
            
            final_state = result if result else {}
            
            artifact_id = final_state.get("artifact_id")
            if artifact_id:
                artifact_content = final_state.get("artifact_content", {})
                
                db.execute(
                    text("""
                        INSERT INTO artifacts (id, run_id, artifact_type, content, meta)
                        VALUES (:id, :run_id, :artifact_type, :content, :meta)
                    """),
                    {
                        "id": artifact_id,
                        "run_id": run_id,
                        "artifact_type": "strategy_document",
                        "content": str(artifact_content),
                        "meta": json.dumps({})
                    }
                )
            
            db.execute(
                text("UPDATE runs SET status = :status WHERE id = :run_id"),
                {"status": "completed", "run_id": run_id}
            )
            db.commit()
            
            return {
                "status": "completed",
                "run_id": run_id,
                "result": final_state,
                "artifact_id": artifact_id
            }
        
        except Exception as e:
            db.execute(
                text("UPDATE runs SET status = :status, error = :error WHERE id = :run_id"),
                {"status": "failed", "error": str(e), "run_id": run_id}
            )
            db.commit()
            raise
        
        finally:
            db.close()
