"""Port/Interface defining the contract for LLM generation capabilities."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from src.core.dtos.llm_provider_dtos import (
    DomainMessageDTO,
    LLMResponseDTO,
    StreamChunkDTO,
    ToolDefinitionDTO,
)


class ILLMProvider(ABC):
    """
    Interface for standardizing LLM interactions across local (e.g., Ollama)
    and cloud (e.g., OpenAI/Anthropic) engines.

    This interface completely hides LangChain's internal message classes and
    JSON schema bindings from the core business logic.
    """

    @abstractmethod
    async def generate_response(
        self,
        messages: List[DomainMessageDTO],
        tools: Optional[List[ToolDefinitionDTO]] = None,
    ) -> LLMResponseDTO:
        """
        Executes a standard conversational generation, optionally binding tools.

        Args:
            messages: The current conversation history mapped to domain DTOs.
            tools: An optional list of JSON schemas defining available system tools.

        Returns:
            LLMResponseDTO containing the text and/or requested tool calls.

        Raises:
            LLMConnectionError: If the engine cannot be reached.
            LLMAuthenticationError: If credentials fail.
            LLMContextLimitExceededError: If the input size exceeds max context.
        """
        pass

    @abstractmethod
    async def stream_response(
        self,
        messages: List[DomainMessageDTO],
        tools: Optional[List[ToolDefinitionDTO]] = None,
    ) -> AsyncIterator[StreamChunkDTO]:
        """
        Yields chunked responses for real-time UI streaming.

        Args:
            messages: The current conversation history.
            tools: Optional tool definitions.

        Yields:
            StreamChunkDTO chunks containing partial content strings.
        """
        pass
