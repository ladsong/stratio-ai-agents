from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from runtime.graphs.conversation_router import build_conversation_router_graph
from runtime.graphs.strategy_synthesis import build_strategy_synthesis_graph


GRAPH_BUILDERS = {
    "conversation_router": build_conversation_router_graph,
    "strategy_synthesis": build_strategy_synthesis_graph,
}


def get_graph(graph_name: str, config: dict[str, Any] | None = None) -> StateGraph:
    if graph_name not in GRAPH_BUILDERS:
        raise ValueError(f"Unknown graph: {graph_name}")
    
    builder = GRAPH_BUILDERS[graph_name]
    return builder(config or {})


def list_available_graphs() -> list[str]:
    return list(GRAPH_BUILDERS.keys())
