from typing import AsyncIterator, Optional, Any
import uuid
from psycopg_pool import AsyncConnectionPool

from langgraph.graph import StateGraph, START, END  # type: ignore
from langchain_core.messages import HumanMessage, AIMessage  # type: ignore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.core.dtos.universal_dtos import ThreadStateDTO
from src.core.enums import Role
from src.core.dtos.llm_provider_dtos import (
    LLMResponseDTO,
    DomainMessageDTO,
    StreamChunkDTO,
)
from src.core.interfaces.ichat_orchestrator import IChatOrchestrator
from src.infra.orchestrators.langgraph.state import AgentState
from src.infra.orchestrators.langgraph.nodes import (
    ToolNode,
    AgentNode,
    EvaluatorNode,
    should_continue,
    should_revise,
)


class LangGraphChatOrchestrator(IChatOrchestrator):
    def __init__(
        self,
        tool_factory: Any,
        llm_provider: Any,
        db_pool: Optional[AsyncConnectionPool] = None,
        max_revisions: int = 2,
    ):
        self.db_pool = db_pool
        self._tool_factory = tool_factory
        self._llm = llm_provider
        self._max_revisions = max_revisions
        self._graph = self._build_graph()
        self.checkpointer = AsyncPostgresSaver(self.db_pool) if self.db_pool else None
        self.app = self._graph.compile(checkpointer=self.checkpointer)

    def _build_graph(self):
        """Constructs the StateGraph with agent, tools, evaluator nodes, and edges."""
        builder = StateGraph(AgentState)

        tools = self._tool_factory.get_all_tools() if self._tool_factory else []

        # Nodes
        builder.add_node(
            "agent", AgentNode(llm=self._llm, tools=tools, max_tokens=4000)
        )
        builder.add_node("tools", ToolNode(tools=tools))
        builder.add_node(
            "evaluator",
            EvaluatorNode(llm=self._llm, max_revisions=self._max_revisions),
        )

        # Normal edges
        builder.add_edge(START, "agent")
        builder.add_edge("tools", "agent")

        # Conditional edges
        builder.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "evaluator": "evaluator",
            },
        )
        builder.add_conditional_edges(
            "evaluator",
            lambda state: should_revise(state, max_revisions=self._max_revisions),
            {
                "agent": "agent",
                "end": END,
            },
        )

        return builder

    async def initialize_database(self) -> None:
        """
        Creates LangGraph's internal `checkpoints` tables.
        Run this ONCE during your App startup.
        """
        if self.db_pool:
            async with AsyncPostgresSaver(self.db_pool) as checkpointer:
                await checkpointer.setup()

    async def process_turn(
        self,
        thread_id: uuid.UUID,
        user_message: DomainMessageDTO,
        config: ThreadStateDTO,
    ) -> LLMResponseDTO:
        # 1. Translate Domain DTO to Langchain Message
        lc_msg = HumanMessage(content=user_message.content)

        # 2. Setup internal execution state
        initial_state = {
            "messages": [lc_msg],
            "config": config,
            "revision_count": 0,
        }
        config_dict = {"configurable": {"thread_id": str(thread_id)}}

        # 3. Execute the graph
        final_state = await self.app.ainvoke(initial_state, config=config_dict)

        # 4. Translate back to Domain DTO
        ai_messages = [m for m in final_state["messages"] if isinstance(m, AIMessage)]
        last_message = ai_messages[-1] if ai_messages else final_state["messages"][-1]
        content = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )
        domain_msg = DomainMessageDTO(role=Role.ASSISTANT, content=str(content))

        return LLMResponseDTO(message=domain_msg, finish_reason="stop")

    async def stream_turn(
        self,
        thread_id: uuid.UUID,
        user_message: DomainMessageDTO,
        config: Any,
    ) -> AsyncIterator[StreamChunkDTO]:
        response = await self.process_turn(thread_id, user_message, config)
        yield StreamChunkDTO(
            content_delta=response.message.content,
            finish_reason=response.finish_reason,
        )
