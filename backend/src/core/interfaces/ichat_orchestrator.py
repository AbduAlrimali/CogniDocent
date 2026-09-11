from abc import ABC, abstractmethod
from typing import AsyncIterator
from uuid import UUID
from src.core.dtos.llm_provider_dtos import (
    DomainMessageDTO,
    LLMResponseDTO,
    StreamChunkDTO,
    SystemAIConfigDTO,
)


class IChatOrchestrator(ABC):
    @abstractmethod
    async def process_turn(
        self, thread_id: UUID, user_message: DomainMessageDTO, config: SystemAIConfigDTO
    ) -> LLMResponseDTO:
        """Executes the complete conversational graph synchronously.

        Raises:
            OrchestratorError: Base class for all orchestration failures.
            GraphRecursionLimitError: If the agent enters an infinite loop or exceeds max steps.
            ContextWindowExceededError: If the conversation history + context exceeds the LLM token budget.
            ProviderUnavailableError: If the underlying LLM provider times out or is unreachable.
            CorruptedThreadStateError: If the checkpointer fails to deserialize or load thread history.
        """
        pass

    @abstractmethod
    async def stream_turn(
        self, thread_id: UUID, user_message: DomainMessageDTO, config: SystemAIConfigDTO
    ) -> AsyncIterator[StreamChunkDTO]:
        """Streams the execution of the conversational graph.

        Raises:
            OrchestratorError: Base class for all orchestration failures.
            GraphRecursionLimitError: If the agent enters an infinite loop or exceeds max steps.
            ContextWindowExceededError: If the conversation history + context exceeds the LLM token budget.
            ProviderUnavailableError: If the underlying LLM provider times out or is unreachable.
            CorruptedThreadStateError: If the checkpointer fails to deserialize or load thread history.
        """
        pass
