from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END


class RouterState(TypedDict):
    thread_id: str
    run_id: str
    messages: list[dict[str, Any]]
    intent: str | None
    route_target: str | None


def classify_intent(state: RouterState) -> RouterState:
    messages = state.get("messages", [])
    
    if not messages:
        state["intent"] = "unknown"
        return state
    
    last_message = messages[-1]
    content = last_message.get("content", "").lower()
    
    if any(word in content for word in ["strategy", "plan", "approach"]):
        state["intent"] = "strategy"
    elif any(word in content for word in ["analyze", "research", "investigate"]):
        state["intent"] = "analysis"
    else:
        state["intent"] = "general"
    
    return state


def route_to_strategy(state: RouterState) -> RouterState:
    intent = state.get("intent", "general")
    
    if intent == "strategy":
        state["route_target"] = "strategy_synthesis"
    elif intent == "analysis":
        state["route_target"] = "analysis_graph"
    else:
        state["route_target"] = "default_handler"
    
    return state


def build_conversation_router_graph(config: dict[str, Any]):
    workflow = StateGraph(RouterState)
    
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("route_to_strategy", route_to_strategy)
    
    workflow.set_entry_point("classify_intent")
    workflow.add_edge("classify_intent", "route_to_strategy")
    workflow.add_edge("route_to_strategy", END)
    
    checkpointer = config.get("checkpointer")
    return workflow.compile(checkpointer=checkpointer)
