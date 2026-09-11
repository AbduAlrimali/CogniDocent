from abc import ABC, abstractmethod
import uuid
from typing import Sequence, Optional, List, Dict, Any
from src.models.document import Document


class IDocumentRepository(ABC):
    """
    Interface for Document repository operations (Port).
    Provides database access primitives for Document records,
    including table of contents (TOC) and document-level metadata.
    """

    @abstractmethod
    async def get_by_id(self, doc_id: uuid.UUID) -> Optional[Document]:
        """Retrieve a document by its ID."""
        pass

    @abstractmethod
    async def get_by_file_hash(self, file_hash: str) -> Optional[Document]:
        """Retrieve a document by its file hash."""
        pass

    @abstractmethod
    async def list_all(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_order: str = "desc",
    ) -> Sequence[Document]:
        """List documents with optional filtering and pagination."""
        pass

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Persist a new document to the database."""
        pass

    @abstractmethod
    async def update(self, doc_id: uuid.UUID, **kwargs) -> Document:
        """Update fields of an existing document."""
        pass

    @abstractmethod
    async def delete(self, doc_id: uuid.UUID) -> bool:
        """Delete a document by its ID."""
        pass

    @abstractmethod
    async def get_document_toc(self, doc_id: uuid.UUID) -> Optional[List[Dict[str, Any]]]:
        """Retrieve the persisted table of contents for a document."""
        pass

    @abstractmethod
    async def get_document_metadata(self, doc_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Retrieve the persisted document header metadata."""
        pass

    @abstractmethod
    async def update_toc(
        self, doc_id: uuid.UUID, toc: List[Dict[str, Any]]
    ) -> Document:
        """Update the table of contents for a document."""
        pass

    @abstractmethod
    async def update_metadata(
        self, doc_id: uuid.UUID, metadata: Dict[str, Any]
    ) -> Document:
        """Update the document header metadata."""
        pass
