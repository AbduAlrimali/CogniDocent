"""Unified LiteLLM Adapter for all cloud and local models."""

from typing import Any, Dict
from langchain_litellm import ChatLiteLLM

from .base_langchain_adapter import BaseLangChainLLMAdapter
from .ilogger import ILogger
from .litellm_config_dtos import LLMRouteConfigDTO, ThinkingLevel, ProviderType


class LiteLLMAdapter(BaseLangChainLLMAdapter):
    """Adapter unifying all LLM providers and injecting reasoning effort payloads via LiteLLM."""

    def __init__(self, config: LLMRouteConfigDTO, logger: ILogger) -> None:
        model_kwargs = self._build_thinking_kwargs(config)
        formatted_model_name = self._format_litellm_model_string(config)

        model = ChatLiteLLM(
            model=formatted_model_name,
            api_key=config.api_key or "sk-no-key",
            api_base=config.base_url,
            temperature=config.temperature,
            model_kwargs=model_kwargs,
        )
        # Pass the initialized model to the base class which handles tool binding and streaming
        super().__init__(
            model=model, provider_name=config.provider.value, logger=logger
        )

    def _format_litellm_model_string(self, config: LLMRouteConfigDTO) -> str:
        """Prepends the provider tag required by LiteLLM routing."""
        if config.provider == ProviderType.OLLAMA:
            return f"ollama/{config.model_name}"
        if config.provider == ProviderType.ANTHROPIC:
            return f"anthropic/{config.model_name}"
        if config.provider == ProviderType.GEMINI:
            return f"gemini/{config.model_name}"

        # OpenAI does not require a prefix in LiteLLM by default
        return config.model_name

    def _build_thinking_kwargs(self, config: LLMRouteConfigDTO) -> Dict[str, Any]:
        """Translates the domain ThinkingLevel into provider-specific API parameters."""
        kwargs: Dict[str, Any] = {}

        if config.thinking_level == ThinkingLevel.NONE:
            return kwargs

        if config.provider == ProviderType.OPENAI and config.model_name.startswith(
            ("o1", "o3")
        ):
            kwargs["reasoning_effort"] = config.thinking_level.value

        elif config.provider == ProviderType.ANTHROPIC and "3-7" in config.model_name:
            budget_map = {
                ThinkingLevel.LOW: 2048,
                ThinkingLevel.MEDIUM: 4096,
                ThinkingLevel.HIGH: 8192,
            }
            budget = budget_map.get(config.thinking_level, 4096)
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }
            # Anthropic enforces that max_tokens must exceed the thinking budget
            kwargs["max_tokens"] = budget + 2000

        return kwargs
