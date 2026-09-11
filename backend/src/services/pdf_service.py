import asyncio
from typing import List, Sequence, Optional, Dict, Any
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.ifast_parser import IFastParser
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.core.interfaces.idocument_repository import IDocumentRepository
from src.core.interfaces.ivision_provider import IVisionProvider
from src.core.interfaces.ilogger import ILogger
from src.core.dtos.fast_parser_dto import TOCItemDTO, FastDocumentMetadataDTO
from src.core.enums import UploadStatus
from src.core.exceptions.database import DocumentNotFoundError
from src.core.exceptions.document_exceptions import DocumentNotParsedError
from src.schemas.document_page import PageUpdateDTO
from src.models.document import Document
from src.models.document_page import DocumentPage


class PDFService:
    """
    Service handling PDF document parsing, page rendering,
    TOC and metadata extraction, hybrid vector retrieval with VLM deep parsing,
    and page embeddings generation.
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        parser: Optional[IFastParser] = None,
        embedding_provider: Optional[IEmbeddingProvider] = None,
        page_repo: Optional[IDocumentPageRepository] = None,
        logger: Optional[ILogger] = None,
        doc_repo: Optional[IDocumentRepository] = None,
        vision_llm: Optional[IVisionProvider] = None,
    ) -> None:
        self.session = session
        self.parser = parser
        self.embedding_provider = embedding_provider
        self.page_repo = page_repo
        self.logger = logger
        self.vision_llm = vision_llm
        if doc_repo is not None:
            self.doc_repo = doc_repo
        elif session is not None and logger is not None:
            from src.infra.repositories.document_repository import DocumentRepository
            self.doc_repo = DocumentRepository(session=session, logger=logger)
        else:
            self.doc_repo = None

    async def _get_file_path(self, doc_id: uuid.UUID) -> Optional[str]:
        if self.doc_repo:
            try:
                doc = await self.doc_repo.get_by_id(doc_id)
                if doc:
                    return doc.file_path if hasattr(doc, "file_path") else str(doc)
            except Exception:
                pass
        if self.session:
            stmt = select(Document.file_path).where(Document.doc_id == doc_id)
            result = await self.session.execute(stmt)
            res = result.scalar_one_or_none()
            if res:
                return res.file_path if hasattr(res, "file_path") else str(res)
        return None

    async def render_page(self, doc_id: uuid.UUID, page_num: int) -> bytes:
        """
        Looks up Document.file_path for doc_id and renders page to image bytes (PNG).
        """
        file_path = await self._get_file_path(doc_id)
        if not file_path:
            if self.logger:
                self.logger.error("Document not found for rendering", doc_id=doc_id, page_num=page_num)
            raise FileNotFoundError(f"Document {doc_id} not found.")

        return await asyncio.to_thread(self.parser.render_page, file_path, page_num)

    async def get_document_toc(self, doc_id: uuid.UUID) -> List[TOCItemDTO]:
        """
        Retrieves TOC for doc_id. If stored in document repository, returns it.
        Otherwise extracts TOC from PDF file using IFastParser, persists it to DB, and returns it.
        """
        if self.doc_repo:
            try:
                toc_data = await self.doc_repo.get_document_toc(doc_id)
                if toc_data is not None:
                    return [
                        TOCItemDTO(
                            title=item["title"],
                            page_num=item["page_num"],
                            level=item.get("level", 1),
                        )
                        for item in toc_data
                    ]
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "Could not retrieve TOC from repository, falling back to file extraction",
                        doc_id=doc_id,
                        exc_info=e,
                    )

        file_path = await self._get_file_path(doc_id)
        if not file_path:
            if self.logger:
                self.logger.error("Document not found for TOC extraction", doc_id=doc_id)
            raise FileNotFoundError(f"Document {doc_id} not found.")

        toc_items = await asyncio.to_thread(self.parser.extract_table_of_contents, file_path)

        if self.doc_repo:
            toc_dicts = [
                {"title": item.title, "page_num": item.page_num, "level": item.level}
                for item in toc_items
            ]
            try:
                await self.doc_repo.update_toc(doc_id, toc_dicts)
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "Failed to persist extracted TOC to repository",
                        doc_id=doc_id,
                        exc_info=e,
                    )

        return toc_items

    async def get_document_metadata(self, doc_id: uuid.UUID) -> FastDocumentMetadataDTO:
        """
        Retrieves metadata for doc_id. If stored in document repository, returns it.
        Otherwise extracts metadata from PDF file using IFastParser, persists it to DB, and returns it.
        """
        if self.doc_repo:
            try:
                meta_data = await self.doc_repo.get_document_metadata(doc_id)
                if meta_data is not None:
                    return FastDocumentMetadataDTO(
                        total_pages=meta_data["total_pages"],
                        file_size_bytes=meta_data.get("file_size_bytes", 0),
                        title=meta_data.get("title"),
                        author=meta_data.get("author"),
                        creator=meta_data.get("creator"),
                        producer=meta_data.get("producer"),
                        custom_metadata=meta_data.get("custom_metadata", {}),
                    )
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "Could not retrieve metadata from repository, falling back to file extraction",
                        doc_id=doc_id,
                        exc_info=e,
                    )

        file_path = await self._get_file_path(doc_id)
        if not file_path:
            if self.logger:
                self.logger.error("Document not found for metadata extraction", doc_id=doc_id)
            raise FileNotFoundError(f"Document {doc_id} not found.")

        metadata_dto = await asyncio.to_thread(self.parser.extract_metadata, file_path)

        if self.doc_repo:
            meta_dict = {
                "total_pages": metadata_dto.total_pages,
                "file_size_bytes": metadata_dto.file_size_bytes,
                "title": metadata_dto.title,
                "author": metadata_dto.author,
                "creator": metadata_dto.creator,
                "producer": metadata_dto.producer,
                "custom_metadata": metadata_dto.custom_metadata,
            }
            try:
                await self.doc_repo.update_metadata(doc_id, meta_dict)
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "Failed to persist extracted metadata to repository",
                        doc_id=doc_id,
                        exc_info=e,
                    )

        return metadata_dto

    async def parse_and_embed_document(self, doc_id: uuid.UUID) -> List[DocumentPage]:
        """
        On project creation: parse document pages, compute embeddings on parsed content,
        and save both to document_pages table. Also populates TOC and metadata in documents table.
        """
        file_path = await self._get_file_path(doc_id)
        if not file_path:
            if self.logger:
                self.logger.error("Document not found for parsing", doc_id=doc_id)
            raise FileNotFoundError(f"Document {doc_id} not found.")

        parsed_doc = await asyncio.to_thread(self.parser.extract_document, file_path)
        if not parsed_doc.pages:
            if self.logger:
                self.logger.warning("Document contains no pages", doc_id=doc_id, file_path=file_path)
            return []

        # Persist TOC and metadata if doc_repo is present
        if self.doc_repo and parsed_doc:
            toc_dicts = [
                {"title": item.title, "page_num": item.page_num, "level": item.level}
                for item in parsed_doc.table_of_contents
            ]
            meta_dict = {
                "total_pages": parsed_doc.metadata.total_pages,
                "file_size_bytes": parsed_doc.metadata.file_size_bytes,
                "title": parsed_doc.metadata.title,
                "author": parsed_doc.metadata.author,
                "creator": parsed_doc.metadata.creator,
                "producer": parsed_doc.metadata.producer,
                "custom_metadata": parsed_doc.metadata.custom_metadata,
            }
            try:
                await self.doc_repo.update(doc_id, status=UploadStatus.COMPLETED, toc=toc_dicts, doc_metadata=meta_dict)
            except Exception as e:
                if self.logger:
                    self.logger.warning("Could not persist TOC and metadata on parse_and_embed", doc_id=doc_id, exc_info=e)

        texts = [p.raw_text for p in parsed_doc.pages]
        embeddings = await self.embedding_provider.embed_batch(texts)

        pages = [
            DocumentPage(
                doc_id=doc_id,
                page_num=p.page_num,
                content=p.raw_text,
                content_vector=emb,
                deep_content=None,
                deep_content_vector=None,
            )
            for p, emb in zip(parsed_doc.pages, embeddings)
        ]

        saved_pages = list(await self.page_repo.bulk_create(pages))
        if self.logger:
            self.logger.info(
                "Parsed and embedded document pages on project creation",
                doc_id=doc_id,
                total_pages=len(saved_pages),
            )
        return saved_pages

    async def get_pages_in_range(
        self, doc_id: uuid.UUID, start_page: int, end_page: int
    ) -> Sequence[DocumentPage]:
        """
        Retrieves document pages within [start_page, end_page] (inclusive).
        - If the document does not exist, raises FileNotFoundError.
        - If the document is not parsed yet, raises DocumentNotParsedError.
        - If parsed, returns pages matching the range from page_repo (empty list if none match).
        """
        doc = None
        if self.doc_repo:
            try:
                doc = await self.doc_repo.get_by_id(doc_id)
            except Exception:
                pass
        if not doc and self.session:
            stmt = select(Document).where(Document.doc_id == doc_id)
            result = await self.session.execute(stmt)
            doc = result.scalar_one_or_none()

        if not doc:
            if self.logger:
                self.logger.error("Document not found for get_pages_in_range", doc_id=doc_id)
            raise FileNotFoundError(f"Document {doc_id} not found.")

        doc_status = getattr(doc, "status", None)
        if doc_status != UploadStatus.COMPLETED:
            if self.logger:
                self.logger.warning(
                    "Document has not been parsed yet",
                    doc_id=doc_id,
                    status=doc_status,
                )
            raise DocumentNotParsedError(
                doc_id=doc_id,
                reason=f"Document status is '{doc_status}', parsing is not completed.",
            )

        if not self.page_repo:
            return []

        pages = list(await self.page_repo.get_pages_in_range(doc_id, start_page, end_page))
        return pages

    async def hybrid_retrieve(
        self,
        doc_id: uuid.UUID,
        query: str,
        limit: int = 3,
    ) -> List[DocumentPage]:
        """
        Use case: Unified vector retrieval with on-demand VLM deep parsing.
        1. Embed the search query.
        2. Execute unified vector search across all document pages: evaluates
           deep_content_vector per page, falling back to content_vector if deep_content_vector is missing.
        3. If no results found, fallback to initial document pages.
        4. For any returned pages lacking deep parsing, concurrently fetch images,
           call Vision LLM to extract markdown into deep_content, compute deep embeddings,
           and save updates to Postgres.
        """
        # 1. Always embed the query first
        query_vector = await self.embedding_provider.embed_text(query)

        # 2. Unified vector search evaluating deep_content_vector falling back to content_vector per page
        pages = list(
            await self.page_repo.search_pages_vector(
                doc_id=doc_id, query_vector=query_vector, limit=limit
            )
        )

        # If no results found from vector search
        if not pages:
            pages = list(await self.page_repo.get_fallback_pages(doc_id=doc_id, limit=limit))

        # 3. Concurrently fetch images and call Vision LLM (Crucial for speed)
        needs_parsing = [p for p in pages if p.deep_content is None]

        if needs_parsing and self.vision_llm:
            async def parse_page(page: DocumentPage) -> DocumentPage:
                image_bytes = await self.render_page(doc_id, page.page_num)
                markdown = await self.vision_llm.extract_markdown(image_bytes)
                page.deep_content = markdown
                return page

            await asyncio.gather(*(parse_page(p) for p in needs_parsing))

            texts = [p.deep_content for p in needs_parsing]
            embeddings = await self.embedding_provider.embed_batch(texts)

            updates: List[PageUpdateDTO] = []
            for p, emb in zip(needs_parsing, embeddings):
                p.deep_content_vector = emb
                updates.append(
                    PageUpdateDTO(
                        page_id=p.page_id,
                        deep_content=p.deep_content,
                        deep_content_vector=emb,
                    )
                )

            # Save the Markdown and Embeddings to Postgres
            await self.page_repo.update_pages(updates)

        return pages
