"""Port/Interface defining the contract for embedding generation capabilities."""

from abc import ABC, abstractmethod
from typing import List


class IEmbeddingProvider(ABC):
    """
    Domain Port for generating text and document embeddings.
    Isolates core business logic and repositories from AI provider specifics.
    """

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single string of text.

        Raises:
            EmbeddingConnectionError: If provider cannot be reached.
            EmbeddingAuthenticationError: If credentials fail.
            EmbeddingRateLimitError: If provider rate limits requests.
            EmbeddingContextLengthExceededError: If text exceeds token context limits.
            EmbeddingDimensionMismatchError: If the returned vector dimensionality is invalid.
            EmbeddingProviderError: Base class for other unexpected provider errors.
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple text strings.

        Raises:
            EmbeddingConnectionError: If provider cannot be reached.
            EmbeddingAuthenticationError: If credentials fail.
            EmbeddingRateLimitError: If provider rate limits requests.
            EmbeddingContextLengthExceededError: If texts exceed token context limits.
            EmbeddingDimensionMismatchError: If any returned vector dimensionality is invalid.
            EmbeddingProviderError: Base class for other unexpected provider errors.
        """
        pass
