import uuid
from typing import Sequence, Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.idocument_repository import IDocumentRepository
from src.core.exceptions.database import (
    RepositoryError,
    DocumentNotFoundError,
    DuplicateDocumentError,
)
from src.models.document import Document


class DocumentRepository(IDocumentRepository):
    """
    SQLAlchemy implementation of IDocumentRepository for PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, doc_id: uuid.UUID) -> Optional[Document]:
        try:
            stmt = select(Document).where(Document.doc_id == doc_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving document by ID",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve document: {str(e)}") from e

    async def get_by_file_hash(self, file_hash: str) -> Optional[Document]:
        try:
            stmt = select(Document).where(Document.file_hash == file_hash)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving document by file hash",
                file_hash=file_hash,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve document by hash: {str(e)}") from e

    async def list_all(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        sort_order: str = "desc",
    ) -> Sequence[Document]:
        try:
            stmt = select(Document)
            if status:
                stmt = stmt.where(Document.status == status)
            if sort_order.lower() == "asc":
                stmt = stmt.order_by(Document.uploaded_at.asc())
            else:
                stmt = stmt.order_by(Document.uploaded_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing documents",
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list documents: {str(e)}") from e

    async def create(self, document: Document) -> Document:
        try:
            self.session.add(document)
            await self.session.commit()
            await self.session.refresh(document)
            return document
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Integrity error creating document (duplicate file_hash)",
                file_hash=document.file_hash,
                exc_info=e,
            )
            raise DuplicateDocumentError("file_hash", document.file_hash) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating document",
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create document: {str(e)}") from e

    async def update(self, doc_id: uuid.UUID, **kwargs) -> Document:
        try:
            doc = await self.get_by_id(doc_id)
            if not doc:
                raise DocumentNotFoundError(doc_id)
            for key, value in kwargs.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)
                elif key == "metadata":
                    setattr(doc, "doc_metadata", value)
            await self.session.commit()
            await self.session.refresh(doc)
            return doc
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error updating document",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to update document: {str(e)}") from e

    async def delete(self, doc_id: uuid.UUID) -> bool:
        try:
            doc = await self.get_by_id(doc_id)
            if not doc:
                raise DocumentNotFoundError(doc_id)
            await self.session.delete(doc)
            await self.session.commit()
            return True
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting document",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete document: {str(e)}") from e

    async def get_document_toc(self, doc_id: uuid.UUID) -> Optional[List[Dict[str, Any]]]:
        try:
            stmt = select(Document.toc).where(Document.doc_id == doc_id)
            result = await self.session.execute(stmt)
            row = result.first()
            if not row:
                raise DocumentNotFoundError(doc_id)
            return row[0]
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving document TOC",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve document TOC: {str(e)}") from e

    async def get_document_metadata(self, doc_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        try:
            stmt = select(Document.doc_metadata).where(Document.doc_id == doc_id)
            result = await self.session.execute(stmt)
            row = result.first()
            if not row:
                raise DocumentNotFoundError(doc_id)
            return row[0]
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving document metadata",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve document metadata: {str(e)}") from e

    async def update_toc(
        self, doc_id: uuid.UUID, toc: List[Dict[str, Any]]
    ) -> Document:
        return await self.update(doc_id, toc=toc)

    async def update_metadata(
        self, doc_id: uuid.UUID, metadata: Dict[str, Any]
    ) -> Document:
        return await self.update(doc_id, doc_metadata=metadata)
