import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.dtos.llm_provider_dtos import EmbeddingConfigDTO
from src.core.enums import EmbeddingProvider
from src.core.interfaces.ilogger import ILogger
from src.core.exceptions.embedding_exceptions import (
    EmbeddingProviderError,
    EmbeddingConnectionError,
    EmbeddingAuthenticationError,
    EmbeddingRateLimitError,
    EmbeddingContextLengthExceededError,
    EmbeddingDimensionMismatchError,
)
from src.infra.llms.litellm_embedding_adapter import LiteLLMEmbeddingAdapter


@pytest.fixture
def mock_logger():
    return MagicMock(spec=ILogger)


@pytest.fixture
def config():
    return EmbeddingConfigDTO(
        provider=EmbeddingProvider.OPENAI,
        model_name="text-embedding-3-small",
        dimensions=1536,
        base_url="https://api.openai.com/v1",
    )


@pytest.fixture
def adapter(config, mock_logger):
    return LiteLLMEmbeddingAdapter(config=config, logger=mock_logger)


@pytest.mark.asyncio
async def test_embed_text_authentication_error(adapter):
    with patch("litellm.aembedding", side_effect=Exception("Unauthorized: 401 Invalid API Key")):
        with pytest.raises(EmbeddingAuthenticationError) as exc_info:
            await adapter.embed_text("test prompt")
        assert "OPENAI" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_text_connection_error(adapter):
    with patch("litellm.aembedding", side_effect=Exception("Connection refused to host: timeout")):
        with pytest.raises(EmbeddingConnectionError) as exc_info:
            await adapter.embed_text("test prompt")
        assert exc_info.value.endpoint == "https://api.openai.com/v1"


@pytest.mark.asyncio
async def test_embed_text_rate_limit_error(adapter):
    with patch("litellm.aembedding", side_effect=Exception("Rate limit exceeded: 429 quota reached")):
        with pytest.raises(EmbeddingRateLimitError) as exc_info:
            await adapter.embed_text("test prompt")
        assert exc_info.value.retry_after_seconds == 60


@pytest.mark.asyncio
async def test_embed_text_context_length_exceeded(adapter):
    with patch("litellm.aembedding", side_effect=Exception("Maximum context length exceeded: too many tokens")):
        with pytest.raises(EmbeddingContextLengthExceededError):
            await adapter.embed_text("test prompt")


@pytest.mark.asyncio
async def test_embed_text_dimension_mismatch(adapter):
    # Model returns 512 dimensions but configured is 1536
    mock_resp = MagicMock()
    mock_resp.data = [{"embedding": [0.1] * 512}]

    with patch("litellm.aembedding", return_value=mock_resp):
        with pytest.raises(EmbeddingDimensionMismatchError) as exc_info:
            await adapter.embed_text("test prompt")
        assert exc_info.value.expected == 1536
        assert exc_info.value.received == 512


@pytest.mark.asyncio
async def test_embed_batch_dimension_mismatch(adapter):
    mock_resp = MagicMock()
    mock_resp.data = [{"embedding": [0.1] * 1536}, {"embedding": [0.2] * 256}]

    with patch("litellm.aembedding", return_value=mock_resp):
        with pytest.raises(EmbeddingDimensionMismatchError) as exc_info:
            await adapter.embed_batch(["text 1", "text 2"])
        assert exc_info.value.expected == 1536
        assert exc_info.value.received == 256


@pytest.mark.asyncio
async def test_embed_text_generic_provider_error(adapter):
    with patch("litellm.aembedding", side_effect=Exception("Unknown internal server malfunction")):
        with pytest.raises(EmbeddingProviderError):
            await adapter.embed_text("test prompt")
