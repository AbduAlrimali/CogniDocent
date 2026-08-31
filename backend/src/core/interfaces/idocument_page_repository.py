from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.models.document_page import DocumentPage


class IDocumentPageRepository(ABC):
    """
    Interface for DocumentPage repository operations (Port).
    Supports retrieving raw text (fast tier), updating rich markdown (deep tier),
    and full-text searching using PostgreSQL search vectors.
    """

    @abstractmethod
    async def get_by_id(self, page_id: uuid.UUID) -> DocumentPage | None:
        """
        Retrieve a page by its ID.
        """
        pass

    @abstractmethod
    async def get_by_page_num(self, doc_id: uuid.UUID, page_num: int) -> DocumentPage | None:
        """
        Retrieve a specific page of a document by page number.
        """
        pass

    @abstractmethod
    async def list_by_document(self, doc_id: uuid.UUID) -> Sequence[DocumentPage]:
        """
        Retrieve all pages for a specific document, ordered by page number.
        """
        pass

    @abstractmethod
    async def create(self, page: DocumentPage) -> DocumentPage:
        """
        Save a new document page.
        """
        pass

    @abstractmethod
    async def update(self, page_id: uuid.UUID, **kwargs) -> DocumentPage:
        """
        Update an existing page (e.g. adding lazy VLM markdown_content).
        """
        pass

    @abstractmethod
    async def delete(self, page_id: uuid.UUID) -> bool:
        """
        Delete a page by its ID.
        """
        pass

    @abstractmethod
    async def search_pages(self, doc_id: uuid.UUID, query: str, limit: int = 10) -> Sequence[DocumentPage]:
        """
        Perform a full-text search using PostgreSQL tsvector indexing over a document's pages.
        """
        pass
