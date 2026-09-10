import uuid
from typing import Sequence, Optional, List, Tuple
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.schemas.document_page import DocumentPageResponse
from src.core.dtos.embedding_dtos import PageEmbeddingUpdateDTO
from src.core.exceptions.database import (
    RepositoryError,
    DocumentPageNotFoundError,
    DuplicatePageError,
)
from src.models.document_page import DocumentPage
from src.models.project import Project
from src.models.embedding_index_metadata import EmbeddingIndexMetadata


class DocumentPageRepository(IDocumentPageRepository):
    """
    SQLAlchemy implementation of IDocumentPageRepository (PostgreSQL Adapter).
    Contains purely database access operations without business logic or orchestration.
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
            self.logger.error("Database error retrieving page by ID", page_id=page_id, exc_info=e)
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
            self.logger.error("Database error retrieving page by page number", doc_id=doc_id, page_num=page_num, exc_info=e)
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
            self.logger.error("Database error listing pages for document", doc_id=doc_id, exc_info=e)
            raise RepositoryError(f"Failed to list pages: {str(e)}") from e

    async def create(self, page: DocumentPage) -> DocumentPage:
        try:
            self.session.add(page)
            await self.session.commit()
            await self.session.refresh(page)
            return page
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning("DocumentPage integrity violation on create", doc_id=page.doc_id, page_num=page.page_num, exc_info=e)
            raise DuplicatePageError("doc_id and page_num combo", f"doc_id={page.doc_id}, page_num={page.page_num}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error("Database error creating document page", doc_id=page.doc_id, page_num=page.page_num, exc_info=e)
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
            self.logger.warning("DocumentPage integrity violation on update", page_id=page_id, exc_info=e)
            raise DuplicatePageError("fields", str(kwargs)) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error("Database error updating page", page_id=page_id, exc_info=e)
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
            self.logger.error("Database error deleting page", page_id=page_id, exc_info=e)
            raise RepositoryError(f"Failed to delete page: {str(e)}") from e

    async def search_pages(self, doc_id: uuid.UUID, query: str, limit: int = 10) -> Sequence[DocumentPage]:
        return await self.search_pages_fts(doc_id=doc_id, query=query, limit=limit)

    async def get_embedding_metadata(self, project_id: uuid.UUID) -> Optional[Tuple[str, int]]:
        try:
            stmt = select(EmbeddingIndexMetadata).where(
                EmbeddingIndexMetadata.project_id == project_id
            )
            result = await self.session.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                return (record.active_model, record.dimensions)
            return None
        except SQLAlchemyError as e:
            self.logger.error("Database error retrieving embedding metadata", project_id=project_id, exc_info=e)
            raise RepositoryError(f"Failed to retrieve embedding metadata: {str(e)}") from e

    async def upsert_embedding_metadata(
        self, project_id: uuid.UUID, active_model: str, dimensions: int
    ) -> None:
        try:
            stmt = select(EmbeddingIndexMetadata).where(
                EmbeddingIndexMetadata.project_id == project_id
            )
            result = await self.session.execute(stmt)
            meta_row = result.scalar_one_or_none()
            if meta_row:
                meta_row.active_model = active_model
                meta_row.dimensions = dimensions
                meta_row.updated_at = func.now()
            else:
                new_meta = EmbeddingIndexMetadata(
                    project_id=project_id,
                    active_model=active_model,
                    dimensions=dimensions,
                )
                self.session.add(new_meta)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error("Database error upserting embedding metadata", project_id=project_id, exc_info=e)
            raise RepositoryError(f"Failed to upsert embedding metadata: {str(e)}") from e

    async def alter_embedding_dimensions(self, new_dimensions: int) -> None:
        try:
            # 1. Drop existing HNSW index
            await self.session.execute(
                text("DROP INDEX IF EXISTS idx_document_pages_embedding;")
            )
            # 2. Alter column type to new vector dimensions with USING NULL
            await self.session.execute(
                text(
                    f"ALTER TABLE document_pages ALTER COLUMN embedding TYPE vector({new_dimensions}) USING NULL;"
                )
            )
            # 3. Recreate HNSW index for cosine distance
            await self.session.execute(
                text(
                    "CREATE INDEX idx_document_pages_embedding ON document_pages USING hnsw (embedding vector_cosine_ops);"
                )
            )
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error("Database error altering embedding dimensions DDL", new_dimensions=new_dimensions, exc_info=e)
            raise RepositoryError(f"Failed to alter embedding dimensions: {str(e)}") from e

    async def nullify_project_embeddings(self, project_id: uuid.UUID) -> None:
        try:
            doc_subquery = select(Project.doc_id).where(Project.project_id == project_id).scalar_subquery()
            await self.session.execute(
                update(DocumentPage)
                .where(DocumentPage.doc_id == doc_subquery)
                .values(embedding=None)
            )
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error("Database error nullifying project embeddings", project_id=project_id, exc_info=e)
            raise RepositoryError(f"Failed to nullify project embeddings: {str(e)}") from e

    async def count_populated_embeddings(self, doc_id: uuid.UUID) -> int:
        try:
            stmt = select(func.count(DocumentPage.page_id)).where(
                DocumentPage.doc_id == doc_id,
                DocumentPage.embedding.isnot(None),
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            self.logger.error("Database error counting populated embeddings", doc_id=doc_id, exc_info=e)
            raise RepositoryError(f"Failed to count populated embeddings: {str(e)}") from e

    async def search_pages_fts(
        self, doc_id: uuid.UUID, query: str, limit: int = 3
    ) -> Sequence[DocumentPage]:
        try:
            tsquery = func.websearch_to_tsquery("english", query)
            stmt = (
                select(DocumentPage)
                .where(
                    DocumentPage.doc_id == doc_id,
                    DocumentPage.search_vector.op("@@")(tsquery),
                )
                .order_by(func.ts_rank_cd(DocumentPage.search_vector, tsquery).desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error("Database error during FTS page search", doc_id=doc_id, query=query, exc_info=e)
            raise RepositoryError(f"FTS search failed: {str(e)}") from e

    async def search_pages_vector(
        self, doc_id: uuid.UUID, query_vector: List[float], limit: int = 3
    ) -> Sequence[DocumentPage]:
        try:
            stmt = (
                select(DocumentPage)
                .where(
                    DocumentPage.doc_id == doc_id,
                    DocumentPage.embedding.isnot(None),
                )
                .order_by(DocumentPage.embedding.cosine_distance(query_vector))
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error("Database error during vector cosine search", doc_id=doc_id, exc_info=e)
            raise RepositoryError(f"Vector search failed: {str(e)}") from e

    async def get_fallback_pages(
        self, doc_id: uuid.UUID, limit: int = 3
    ) -> Sequence[DocumentPage]:
        try:
            stmt = (
                select(DocumentPage)
                .where(DocumentPage.doc_id == doc_id)
                .order_by(DocumentPage.page_num.asc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error("Database error fetching fallback pages", doc_id=doc_id, exc_info=e)
            raise RepositoryError(f"Fallback fetch failed: {str(e)}") from e

    async def get_pages_missing_embeddings(
        self,
        project_id: uuid.UUID,
        batch_size: int = 100,
    ) -> List[DocumentPageResponse]:
        try:
            stmt = (
                select(DocumentPage)
                .join(Project, Project.doc_id == DocumentPage.doc_id)
                .where(
                    Project.project_id == project_id,
                    DocumentPage.embedding.is_(None),
                )
                .order_by(DocumentPage.page_num.asc())
                .limit(batch_size)
            )
            result = await self.session.execute(stmt)
            pages = result.scalars().all()
            return [DocumentPageResponse.model_validate(p) for p in pages]
        except SQLAlchemyError as e:
            self.logger.error("Database error fetching pages missing embeddings", project_id=project_id, exc_info=e)
            raise RepositoryError(f"Failed to fetch pages missing embeddings: {str(e)}") from e

    async def update_page_embeddings(
        self, updates: Sequence[PageEmbeddingUpdateDTO]
    ) -> None:
        if not updates:
            return
        try:
            for item in updates:
                await self.session.execute(
                    update(DocumentPage)
                    .where(DocumentPage.page_id == item.page_id)
                    .values(embedding=item.embedding)
                )
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error("Database error updating page embeddings", count=len(updates), exc_info=e)
            raise RepositoryError(f"Failed to update page embeddings: {str(e)}") from e
