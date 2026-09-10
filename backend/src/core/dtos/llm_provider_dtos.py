"""Data Transfer Objects for the LLM Provider domain boundary."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.core.enums import Role, ThinkingLevel, ChatProvider, EmbeddingProvider
from pydantic import Field


@dataclass(frozen=True)
class ToolCallDTO:
    """Represents a structured request from the LLM to execute a tool."""

    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass(frozen=True)
class ToolDefinitionDTO:
    """A pure domain representation of a tool's JSON schema signature."""

    name: str
    description: str
    parameters_schema: Dict[str, Any]


@dataclass(frozen=True)
class DomainMessageDTO:
    """A provider-agnostic representation of a conversation message."""

    role: Role
    content: str
    tool_calls: List[ToolCallDTO] = field(default_factory=list)
    tool_call_id: Optional[str] = None  # Used when role == TOOL


@dataclass(frozen=True)
class LLMResponseDTO:
    """The final payload returned by the LLM Provider."""

    message: DomainMessageDTO
    finish_reason: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class StreamChunkDTO:
    """A generic streaming chunk to pass back to the API."""

    content_delta: str = ""
    tool_name: Optional[str] = None
    finish_reason: Optional[str] = None


@dataclass(frozen=True)
class BaseLLMConfigDTO:
    """The active routing configuration retrieved from the user's database settings."""

    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass(frozen=True)
class LLMRouteConfigDTO(BaseLLMConfigDTO):
    """The active routing configuration retrieved from the user's database settings."""

    provider: ChatProvider = ChatProvider.OPENAI
    temperature: float = 0.0
    thinking_level: ThinkingLevel = ThinkingLevel.NONE


@dataclass(frozen=True)
class EmbeddingConfigDTO(BaseLLMConfigDTO):
    """Configuration for the active embedding engine."""

    provider: EmbeddingProvider = EmbeddingProvider.OPENAI
    dimensions: int = 768
    timeout_seconds: int = 60


@dataclass(frozen=True)
class SystemAIConfigDTO:
    # Swapped frequently by the user in UI
    active_chat_model: LLMRouteConfigDTO
    embedding_config: EmbeddingConfigDTO
