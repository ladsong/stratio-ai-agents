from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.types import Interrupt


class StrategyState(TypedDict):
    thread_id: str
    run_id: str
    messages: list[dict[str, Any]]
    context: dict[str, Any] | None
    strategy: str | None
    approval_status: str | None
    approval_response: dict[str, Any] | None
    artifact_id: str | None


def analyze_context(state: StrategyState) -> StrategyState:
    messages = state.get("messages", [])
    
    context = {
        "message_count": len(messages),
        "topics": [],
        "sentiment": "neutral"
    }
    
    if messages:
        last_message = messages[-1]
        content = last_message.get("content", "")
        
        if "strategy" in content.lower():
            context["topics"].append("strategy")
        if "plan" in content.lower():
            context["topics"].append("planning")
    
    state["context"] = context
    return state


def generate_strategy(state: StrategyState) -> StrategyState:
    context = state.get("context", {})
    topics = context.get("topics", [])
    
    if "strategy" in topics:
        strategy = "Strategic approach: Focus on long-term planning and execution"
    elif "planning" in topics:
        strategy = "Planning approach: Break down into actionable steps"
    else:
        strategy = "General approach: Analyze and recommend next steps"
    
    state["strategy"] = strategy
    return state


def request_approval(state: StrategyState) -> StrategyState:
    strategy = state.get("strategy", "")
    
    approval_payload = {
        "type": "strategy_approval",
        "strategy": strategy,
        "context": state.get("context", {}),
        "question": "Do you approve this strategy approach?"
    }
    
    raise Interrupt(approval_payload)


def create_artifact(state: StrategyState) -> StrategyState:
    import uuid
    
    approval_status = state.get("approval_status", "pending")
    
    if approval_status != "approved":
        state["artifact_id"] = None
        return state
    
    artifact_id = str(uuid.uuid4())
    
    artifact_content = {
        "type": "strategy_document",
        "strategy": state.get("strategy", ""),
        "context": state.get("context", {}),
        "approved_at": "2026-03-05T23:00:00Z",
        "approval_response": state.get("approval_response", {})
    }
    
    state["artifact_id"] = artifact_id
    state["artifact_content"] = artifact_content
    
    return state


def should_create_artifact(state: StrategyState) -> str:
    approval_status = state.get("approval_status", "pending")
    
    if approval_status == "approved":
        return "create_artifact"
    else:
        return END


def build_strategy_synthesis_graph(config: dict[str, Any]):
    workflow = StateGraph(StrategyState)
    
    workflow.add_node("analyze_context", analyze_context)
    workflow.add_node("generate_strategy", generate_strategy)
    workflow.add_node("request_approval", request_approval)
    workflow.add_node("create_artifact", create_artifact)
    
    workflow.set_entry_point("analyze_context")
    workflow.add_edge("analyze_context", "generate_strategy")
    workflow.add_edge("generate_strategy", "request_approval")
    
    workflow.add_conditional_edges(
        "request_approval",
        should_create_artifact,
        {
            "create_artifact": "create_artifact",
            END: END
        }
    )
    
    workflow.add_edge("create_artifact", END)
    
    checkpointer = config.get("checkpointer")
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["request_approval"])
