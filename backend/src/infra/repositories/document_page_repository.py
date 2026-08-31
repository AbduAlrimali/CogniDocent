import uuid
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.core.exceptions.database import (
    RepositoryError,
    DocumentPageNotFoundError,
    DuplicatePageError,
)
from src.models.document_page import DocumentPage


class DocumentPageRepository(IDocumentPageRepository):
    """
    SQLAlchemy implementation of the IDocumentPageRepository for PostgreSQL.
    Supports fast text indexing, VLM lazy cache updating, and PostgreSQL full-text search.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, page_id: uuid.UUID) -> DocumentPage | None:
        try:
            stmt = select(DocumentPage).where(DocumentPage.page_id == page_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving page by ID",
                page_id=page_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve page: {str(e)}") from e

    async def get_by_page_num(self, doc_id: uuid.UUID, page_num: int) -> DocumentPage | None:
        try:
            stmt = select(DocumentPage).where(
                DocumentPage.doc_id == doc_id,
                DocumentPage.page_num == page_num,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving page by page number",
                doc_id=doc_id,
                page_num=page_num,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve page: {str(e)}") from e

    async def list_by_document(self, doc_id: uuid.UUID) -> Sequence[DocumentPage]:
        try:
            stmt = (
                select(DocumentPage)
                .where(DocumentPage.doc_id == doc_id)
                .order_by(DocumentPage.page_num.asc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing pages for document",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list pages: {str(e)}") from e

    async def create(self, page: DocumentPage) -> DocumentPage:
        try:
            # Let the database generate the search vector automatically or handle it
            self.session.add(page)
            await self.session.commit()
            await self.session.refresh(page)
            return page
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "DocumentPage integrity violation on create",
                doc_id=page.doc_id,
                page_num=page.page_num,
                exc_info=e,
            )
            raise DuplicatePageError(
                "doc_id and page_num combo",
                f"doc_id={page.doc_id}, page_num={page.page_num}",
            ) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating document page",
                doc_id=page.doc_id,
                page_num=page.page_num,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create page: {str(e)}") from e

    async def update(self, page_id: uuid.UUID, **kwargs) -> DocumentPage:
        try:
            page = await self.get_by_id(page_id)
            if not page:
                raise DocumentPageNotFoundError(page_id)

            for key, value in kwargs.items():
                if hasattr(page, key):
                    setattr(page, key, value)

            await self.session.commit()
            await self.session.refresh(page)
            return page
        except DocumentPageNotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "DocumentPage integrity violation on update",
                page_id=page_id,
                exc_info=e,
            )
            raise DuplicatePageError("fields", str(kwargs)) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error updating page",
                page_id=page_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to update page: {str(e)}") from e

    async def delete(self, page_id: uuid.UUID) -> bool:
        try:
            page = await self.get_by_id(page_id)
            if not page:
                return False

            await self.session.delete(page)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting page",
                page_id=page_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete page: {str(e)}") from e

    async def search_pages(self, doc_id: uuid.UUID, query: str, limit: int = 10) -> Sequence[DocumentPage]:
        try:
            # Performs PostgreSQL full-text search against the 'search_vector' using websearch or plain match
            stmt = (
                select(DocumentPage)
                .where(
                    DocumentPage.doc_id == doc_id,
                    DocumentPage.search_vector.op("@@")(
                        func.websearch_to_tsquery("english", query)
                    ),
                )
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error during full-text page search",
                doc_id=doc_id,
                query=query,
                exc_info=e,
            )
            raise RepositoryError(f"FTS search failed: {str(e)}") from e
