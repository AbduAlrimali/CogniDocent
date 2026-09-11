"""Adapter implementing IEmbeddingProvider using LiteLLM."""

from typing import List
import litellm

from src.core.dtos.llm_provider_dtos import EmbeddingConfigDTO
from src.core.enums import EmbeddingProvider
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.core.interfaces.ilogger import ILogger
from src.core.exceptions.embedding_exceptions import (
    EmbeddingProviderError,
    EmbeddingConnectionError,
    EmbeddingAuthenticationError,
    EmbeddingRateLimitError,
    EmbeddingContextLengthExceededError,
    EmbeddingDimensionMismatchError,
)


class LiteLLMEmbeddingAdapter(IEmbeddingProvider):
    """
    Adapter using LiteLLM to standardize embedding calls across local (Ollama)
    and cloud providers (OpenAI, Gemini, Cohere, Voyage).
    Translates raw library/HTTP errors into domain embedding exceptions.
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
            embedding: List[float] = response.data[0]["embedding"]

            if self.config.dimensions and len(embedding) != self.config.dimensions:
                raise EmbeddingDimensionMismatchError(
                    expected=self.config.dimensions,
                    received=len(embedding),
                    model_name=self.formatted_model_name,
                )

            return embedding
        except EmbeddingProviderError:
            raise
        except Exception as e:
            self._handle_exception(e)

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
            embeddings: List[List[float]] = [item["embedding"] for item in response.data]

            if self.config.dimensions:
                for emb in embeddings:
                    if len(emb) != self.config.dimensions:
                        raise EmbeddingDimensionMismatchError(
                            expected=self.config.dimensions,
                            received=len(emb),
                            model_name=self.formatted_model_name,
                        )

            return embeddings
        except EmbeddingProviderError:
            raise
        except Exception as e:
            self._handle_exception(e)

    def _handle_exception(self, exc: Exception) -> None:
        """Translates provider and library-level errors into domain exceptions."""
        exc_str = str(exc).lower()
        provider_name = self.config.provider.value

        self.logger.error(
            f"{provider_name} embedding request failed",
            exc_info=exc,
            provider=provider_name,
            model=self.formatted_model_name,
            error=str(exc),
        )

        if any(term in exc_str for term in ["auth", "api_key", "unauthorized", "forbidden", "401", "403"]):
            raise EmbeddingAuthenticationError(provider_name) from exc
        if any(term in exc_str for term in ["rate limit", "429", "quota", "resource_exhausted"]):
            raise EmbeddingRateLimitError(retry_after_seconds=60) from exc
        if any(term in exc_str for term in ["context length", "maximum context", "token limit", "too many tokens", "max_tokens", "maximum sequence length"]):
            raise EmbeddingContextLengthExceededError() from exc
        if any(term in exc_str for term in ["connection", "refused", "unreachable", "timeout", "timed out", "connecterror"]):
            raise EmbeddingConnectionError(
                provider_name, endpoint=self.config.base_url or "configured endpoint"
            ) from exc

        raise EmbeddingProviderError(f"{provider_name} embedding error: {exc}") from exc
