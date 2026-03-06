"""Nanobot agent executor with tool policy enforcement."""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus
from nanobot.providers.litellm_provider import LiteLLMProvider
from core.repositories.tool_policy_repo import ToolPolicyRepository


class NanobotExecutor:
    """Executor that wraps nanobot's AgentLoop with policy enforcement."""
    
    def __init__(self):
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://nanobot:nanobot@postgres:5432/nanobot"
        )
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        self.workspace = Path("/workspace")
        self.skills_dir = Path("/nanobot/nanobot/skills")
        
        self.provider = LiteLLMProvider(
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        
        self.bus = MessageBus()
        
        self.model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "40"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.1"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
    
    def _create_agent_with_policies(
        self, 
        thread_id: str, 
        workspace_id: str | None = None
    ) -> AgentLoop:
        """Create AgentLoop with tools filtered by policy."""
        from nanobot.agent.tools.filesystem import (
            ReadFileTool, WriteFileTool, EditFileTool, ListDirTool
        )
        from nanobot.agent.tools.shell import ExecTool
        from nanobot.agent.tools.web import WebSearchTool, WebFetchTool
        from nanobot.agent.tools.message import MessageTool
        
        db = self.SessionLocal()
        try:
            policy_repo = ToolPolicyRepository(db)
            allowed_tools = policy_repo.get_allowed_tools(thread_id, workspace_id)
        finally:
            db.close()
        
        agent = AgentLoop(
            bus=self.bus,
            provider=self.provider,
            workspace=self.workspace,
            model=self.model,
            max_iterations=self.max_iterations,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            memory_window=100,
            restrict_to_workspace=False,
        )
        
        agent.tools._tools.clear()
        
        if "read_file" in allowed_tools:
            agent.tools.register(ReadFileTool(
                workspace=self.workspace,
                allowed_dir=self.skills_dir
            ))
        
        if "write_file" in allowed_tools:
            agent.tools.register(WriteFileTool(
                workspace=self.workspace,
                allowed_dir=self.skills_dir
            ))
        
        if "edit_file" in allowed_tools:
            agent.tools.register(EditFileTool(
                workspace=self.workspace,
                allowed_dir=self.skills_dir
            ))
        
        if "list_dir" in allowed_tools:
            agent.tools.register(ListDirTool(
                workspace=self.workspace,
                allowed_dir=self.skills_dir
            ))
        
        if "exec" in allowed_tools:
            agent.tools.register(ExecTool(
                working_dir=str(self.workspace),
                timeout=30,
                restrict_to_workspace=False,
            ))
        
        if "web_search" in allowed_tools:
            agent.tools.register(WebSearchTool(
                api_key=os.getenv("BRAVE_API_KEY"),
                proxy=os.getenv("WEB_PROXY"),
            ))
        
        if "fetch_url" in allowed_tools:
            agent.tools.register(WebFetchTool(
                proxy=os.getenv("WEB_PROXY"),
            ))
        
        if "message" in allowed_tools:
            agent.tools.register(MessageTool(
                send_callback=self.bus.publish_outbound
            ))
        
        return agent
    
    async def execute_graph(
        self,
        run_id: str,
        thread_id: str,
        graph_name: str,
        initial_state: dict[str, Any],
        config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute using nanobot agent with policy enforcement."""
        db = self.SessionLocal()
        
        try:
            db.execute(
                text("UPDATE runs SET status = :status WHERE id = :run_id"),
                {"status": "running", "run_id": run_id}
            )
            db.commit()
            
            workspace_id = None
            thread = db.execute(
                text("SELECT meta FROM threads WHERE id = :thread_id"),
                {"thread_id": thread_id}
            ).fetchone()
            if thread and thread[0]:
                workspace_id = thread[0].get("workspace_id")
            
            agent = self._create_agent_with_policies(thread_id, workspace_id)
            
            message = initial_state.get("message", "")
            if not message and "messages" in initial_state:
                messages = initial_state["messages"]
                if messages and isinstance(messages[-1], dict):
                    message = messages[-1].get("content", "")
            
            response = await agent.process_direct(
                content=message,
                session_key=thread_id,
            )
            
            artifact_id = str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO artifacts (id, run_id, artifact_type, content, created_at)
                    VALUES (:id, :run_id, :artifact_type, :content, NOW())
                """),
                {
                    "id": artifact_id,
                    "run_id": run_id,
                    "artifact_type": "message",
                    "content": response
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
                "result": {"response": response}
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
    
    async def resume_graph(
        self,
        run_id: str,
        thread_id: str,
        graph_name: str,
        approval_response: dict[str, Any]
    ) -> dict[str, Any]:
        """Resume execution (not implemented yet - future feature)."""
        raise NotImplementedError("Resume not yet implemented for NanobotExecutor")
