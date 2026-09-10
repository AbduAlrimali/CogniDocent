"""Data Transfer Objects for embedding operations between domains and use cases."""

from dataclasses import dataclass
from typing import List, Optional
import uuid


@dataclass(frozen=True)
class EmbeddingVectorDTO:
    """
    Domain DTO / Value Object representing an embedding vector.
    Carries the numerical vector values alongside optional model provenance.
    """

    values: List[float]
    model_name: Optional[str] = None

    @property
    def dimensions(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class PageEmbeddingUpdateDTO:
    """
    Domain DTO representing an embedding update payload for a document page.
    Eliminates primitive obsession (tuples) across domain ports and adapters.
    """

    page_id: uuid.UUID
    embedding: List[float]
