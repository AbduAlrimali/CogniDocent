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
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple text strings.
        """
        pass
