from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver


def get_checkpoint_saver() -> MemorySaver:
    return MemorySaver()
