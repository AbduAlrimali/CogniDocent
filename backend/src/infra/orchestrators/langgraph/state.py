from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages  # type: ignore
from src.core.dtos.universal_dtos import ThreadStateDTO


class AgentState(TypedDict):
    """Internal graph state, hidden from the domain."""

    messages: Annotated[list, add_messages]
    config: ThreadStateDTO
    revision_count: int
