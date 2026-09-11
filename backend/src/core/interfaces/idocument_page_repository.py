from abc import ABC, abstractmethod
import uuid
from typing import Sequence, Optional, List, Tuple
from src.models.document_page import DocumentPage
from src.schemas.document_page import DocumentPageResponse, PageUpdateDTO


class IDocumentPageRepository(ABC):
    """
    Interface for DocumentPage repository operations (Port).
    Provides dumb database access primitives for DocumentPages and embedding metadata.
    Contains no business logic or orchestration.
    """

    @abstractmethod
    async def get_by_id(self, page_id: uuid.UUID) -> DocumentPage | None:
        """Retrieve a page by its ID."""
        pass

    @abstractmethod
    async def get_by_page_num(self, doc_id: uuid.UUID, page_num: int) -> DocumentPage | None:
        """Retrieve a specific page of a document by page number."""
        pass

    @abstractmethod
    async def list_by_document(self, doc_id: uuid.UUID) -> Sequence[DocumentPage]:
        """Retrieve all pages for a specific document, ordered by page number."""
        pass

    @abstractmethod
    async def get_pages_in_range(
        self, doc_id: uuid.UUID, start_page: int, end_page: int
    ) -> Sequence[DocumentPage]:
        """Retrieve document pages within the range [start_page, end_page] inclusive, ordered by page_num."""
        pass

    @abstractmethod
    async def create(self, page: DocumentPage) -> DocumentPage:
        """Save a new document page."""
        pass

    @abstractmethod
    async def bulk_create(self, pages: Sequence[DocumentPage]) -> Sequence[DocumentPage]:
        """Bulk save document pages."""
        pass

    @abstractmethod
    async def update(self, page_id: uuid.UUID, **kwargs) -> DocumentPage:
        """Update an existing page."""
        pass

    @abstractmethod
    async def delete(self, page_id: uuid.UUID) -> bool:
        """Delete a page by its ID."""
        pass

    @abstractmethod
    async def get_embedding_metadata(self, project_id: uuid.UUID) -> Optional[Tuple[str, int]]:
        """Retrieve active embedding model name and dimensions for a project."""
        pass

    @abstractmethod
    async def upsert_embedding_metadata(
        self, project_id: uuid.UUID, active_model: str, dimensions: int
    ) -> None:
        """Upsert embedding metadata record for a project."""
        pass

    @abstractmethod
    async def alter_embedding_dimensions(self, new_dimensions: int) -> None:
        """
        Execute DDL routine to alter pgvector column dimensions for content_vector and deep_content_vector:
        1. DROP INDEX IF EXISTS idx_document_pages_content_vector;
        2. DROP INDEX IF EXISTS idx_document_pages_deep_content_vector;
        3. ALTER TABLE document_pages ALTER COLUMN content_vector TYPE vector(:new_dimensions) USING NULL;
        4. ALTER TABLE document_pages ALTER COLUMN deep_content_vector TYPE vector(:new_dimensions) USING NULL;
        5. Rebuild HNSW indexes.
        """
        pass

    @abstractmethod
    async def nullify_project_embeddings(self, project_id: uuid.UUID) -> None:
        """
        Execute DML update setting content_vector = NULL and deep_content_vector = NULL for the document belonging to project_id.
        """
        pass

    @abstractmethod
    async def count_populated_embeddings(self, doc_id: uuid.UUID) -> int:
        """Count how many pages for doc_id have non-null content_vector or deep_content_vector."""
        pass

    @abstractmethod
    async def search_pages_vector(
        self, doc_id: uuid.UUID, query_vector: List[float], limit: int = 3
    ) -> Sequence[DocumentPage]:
        """
        Execute unified vector search across all pages: evaluates deep_content_vector per page,
        falling back to content_vector if deep_content_vector is not present.
        """
        pass

    @abstractmethod
    async def get_fallback_pages(
        self, doc_id: uuid.UUID, limit: int = 3
    ) -> Sequence[DocumentPage]:
        """Fetch the first N pages of a document ordered by page_num."""
        pass

    @abstractmethod
    async def get_pages_missing_embeddings(
        self,
        project_id: uuid.UUID,
        batch_size: int = 100,
    ) -> List[DocumentPageResponse]:
        """Fetches rows where content_vector IS NULL for the specified project."""
        pass

    @abstractmethod
    async def update_pages(
        self, updates: Sequence[PageUpdateDTO]
    ) -> None:
        """Batch update document pages with deep_content and deep_content_vector."""
        pass
