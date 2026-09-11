"""Domain exceptions for Embedding Provider interactions."""

from typing import Optional


class EmbeddingProviderError(Exception):
    """Base exception for all embedding generation failures."""

    def __init__(self, message: str = "An error occurred during embedding generation."):
        self.message = message
        super().__init__(self.message)


class EmbeddingConnectionError(EmbeddingProviderError):
    """Raised when the embedding provider is unreachable (e.g. Ollama is down or timeout)."""

    def __init__(self, provider_name: str, endpoint: Optional[str] = None):
        endpoint_info = f" at {endpoint}" if endpoint else ""
        super().__init__(f"Failed to connect to {provider_name}{endpoint_info}.")
        self.provider_name = provider_name
        self.endpoint = endpoint


class EmbeddingAuthenticationError(EmbeddingProviderError):
    """Raised when cloud provider API keys are invalid, unauthorized, or missing."""

    def __init__(self, provider_name: str):
        super().__init__(
            f"Authentication failed for embedding provider: {provider_name}. Check API keys."
        )
        self.provider_name = provider_name


class EmbeddingRateLimitError(EmbeddingProviderError):
    """Raised when an embedding provider throttles or rate-limits requests."""

    def __init__(self, retry_after_seconds: Optional[int] = None):
        retry_msg = f" Retry after {retry_after_seconds} seconds." if retry_after_seconds else ""
        super().__init__(f"Embedding rate limit exceeded.{retry_msg}")
        self.retry_after_seconds = retry_after_seconds


class EmbeddingContextLengthExceededError(EmbeddingProviderError):
    """Raised when input text exceeds the embedding model context/token limit."""

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        requested_tokens: Optional[int] = None,
    ):
        if max_tokens and requested_tokens:
            msg = f"Embedding context limit exceeded. Model allows {max_tokens}, but input requires {requested_tokens}."
        else:
            msg = "Input text exceeds the maximum context length for the embedding model."
        super().__init__(msg)
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens


class EmbeddingDimensionMismatchError(EmbeddingProviderError):
    """Raised when the generated embedding vector dimensionality does not match the configured schema."""

    def __init__(self, expected: int, received: int, model_name: str):
        super().__init__(
            f"Embedding dimension mismatch for model '{model_name}': expected {expected} dimensions, but received {received}."
        )
        self.expected = expected
        self.received = received
        self.model_name = model_name
