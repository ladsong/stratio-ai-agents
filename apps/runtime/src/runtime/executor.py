from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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
    
    def execute_graph(
        self,
        run_id: str,
        thread_id: str,
        graph_name: str,
        initial_state: dict[str, Any],
        config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        db = get_db_session()
        
        try:
            db.execute(
                text("UPDATE runs SET status = :status WHERE id = :run_id"),
                {"status": "running", "run_id": run_id}
            )
            db.commit()
            
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
                            "meta": {}
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
        db = get_db_session()
        
        try:
            db.execute(
                text("UPDATE runs SET status = :status WHERE id = :run_id"),
                {"status": "running", "run_id": run_id}
            )
            db.commit()
            
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
                        "meta": {}
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
