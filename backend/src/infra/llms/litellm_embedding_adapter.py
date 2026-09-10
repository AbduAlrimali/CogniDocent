"""Adapter implementing IEmbeddingProvider using LiteLLM."""

from typing import List
import litellm

from src.core.dtos.llm_provider_dtos import EmbeddingConfigDTO
from src.core.enums import EmbeddingProvider
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.core.interfaces.ilogger import ILogger


class LiteLLMEmbeddingAdapter(IEmbeddingProvider):
    """
    Adapter using LiteLLM to standardize embedding calls across local (Ollama)
    and cloud providers (OpenAI, Gemini, Cohere, Voyage).
    """

    def __init__(self, config: EmbeddingConfigDTO, logger: ILogger) -> None:
        self.config = config
        self.logger = logger
        self.formatted_model_name = self._format_model_name(config)

    def _format_model_name(self, config: EmbeddingConfigDTO) -> str:
        if config.provider == EmbeddingProvider.OLLAMA:
            return f"ollama/{config.model_name}"
        if config.provider == EmbeddingProvider.GEMINI:
            return f"gemini/{config.model_name}"
        if config.provider == EmbeddingProvider.VOYAGE:
            return f"voyage/{config.model_name}"
        if config.provider == EmbeddingProvider.COHERE:
            return f"cohere/{config.model_name}"
        return config.model_name

    async def embed_text(self, text: str) -> List[float]:
        try:
            kwargs = {
                "model": self.formatted_model_name,
                "input": [text],
                "timeout": self.config.timeout_seconds,
            }
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["api_base"] = self.config.base_url

            response = await litellm.aembedding(**kwargs)
            return response.data[0]["embedding"]
        except Exception as e:
            self.logger.error(
                "Failed to generate embedding for text",
                model=self.formatted_model_name,
                exc_info=e,
            )
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            kwargs = {
                "model": self.formatted_model_name,
                "input": texts,
                "timeout": self.config.timeout_seconds,
            }
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["api_base"] = self.config.base_url

            response = await litellm.aembedding(**kwargs)
            return [item["embedding"] for item in response.data]
        except Exception as e:
            self.logger.error(
                "Failed to generate embeddings batch",
                model=self.formatted_model_name,
                batch_size=len(texts),
                exc_info=e,
            )
            raise
