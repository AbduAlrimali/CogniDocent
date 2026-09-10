"""Services and use cases for project embedding lifecycle management."""

from typing import Optional, List, Tuple
import uuid

from src.core.dtos.llm_provider_dtos import EmbeddingConfigDTO
from src.core.dtos.embedding_dtos import PageEmbeddingUpdateDTO
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.core.interfaces.ilogger import ILogger
from src.models.document_page import DocumentPage


class EmbeddingService:
    """
    Use cases orchestrating project embedding model changes, hybrid retrieval with fallback,
    and background re-embedding routines.
    """

    def __init__(
        self,
        document_page_repo: IDocumentPageRepository,
        embedding_provider: IEmbeddingProvider,
        logger: ILogger,
    ) -> None:
        self.repo = document_page_repo
        self.embedding_provider = embedding_provider
        self.logger = logger

    async def update_project_embedding_model(
        self, project_id: uuid.UUID, config: EmbeddingConfigDTO
    ) -> None:
        """
        Use case: updates the embedding model for a project.
        Business rules:
        - Reads metadata from DB.
        - If metadata is empty or active_model != config.model_name or dimensions changed:
          - If dimensions differ: executes DDL routine to alter pgvector column and rebuild HNSW index.
          - If dimensions are identical: nullifies embeddings only for the related document.
          - Upserts embedding_index_metadata for project_id.
        """
        current_meta = await self.repo.get_embedding_metadata(project_id)
        current_model = current_meta[0] if current_meta else None
        current_dim = current_meta[1] if current_meta else 768

        if current_model != config.model_name or current_dim != config.dimensions:
            self.logger.info(
                "Project embedding model change detected. Executing reset routine.",
                project_id=project_id,
                current_model=current_model,
                new_model=config.model_name,
                current_dim=current_dim,
                new_dim=config.dimensions,
            )

            # Check if dimension change requires table column alteration
            if current_dim != config.dimensions:
                self.logger.info(
                    "Altering pgvector column dimension and rebuilding index",
                    old_dim=current_dim,
                    new_dim=config.dimensions,
                )
                await self.repo.alter_embedding_dimensions(config.dimensions)
            else:
                self.logger.info(
                    "Nullifying embeddings for project document",
                    project_id=project_id,
                )
                await self.repo.nullify_project_embeddings(project_id)

            await self.repo.upsert_embedding_metadata(
                project_id=project_id,
                active_model=config.model_name,
                dimensions=config.dimensions,
            )
        else:
            self.logger.info(
                "Project embedding model unchanged. No reset needed.",
                project_id=project_id,
                active_model=config.model_name,
            )

    async def hybrid_retrieve(
        self,
        doc_id: uuid.UUID,
        query: str,
        limit: int = 3,
    ) -> List[DocumentPage]:
        """
        Use case: Hybrid Retrieval Fallback.
        Business rules:
        1. Check if the document pages have embedding IS NULL or if all embeddings are unpopulated.
        2. If embeddings are unpopulated, bypass vector cosine calculation and query strictly
           against full-text search (tsquery). Pick 3 best pages, and if any page is not embedded
           using a model, generate its vector embeddings on-the-fly and store in the DB.
        3. If embeddings are populated, generate the query vector using the embedding provider
           and execute vector cosine similarity search. Lazily embed any returned page lacking embeddings.
        """
        populated_count = await self.repo.count_populated_embeddings(doc_id)

        if populated_count == 0:
            self.logger.info(
                "Embeddings unpopulated for document; bypassing vector search and falling back to FTS",
                doc_id=doc_id,
            )
            pages = list(await self.repo.search_pages_fts(doc_id=doc_id, query=query, limit=limit))
            if not pages:
                pages = list(await self.repo.get_fallback_pages(doc_id=doc_id, limit=limit))

            # Pick 3 best pages and if any page is not embedded, generate vector embeddings and store in DB
            unembedded = [p for p in pages if p.embedding is None]
            if unembedded:
                self.logger.info(
                    "Lazily embedding retrieved pages on-the-fly",
                    doc_id=doc_id,
                    count=len(unembedded),
                )
                texts = [p.markdown_content or p.content for p in unembedded]
                embeddings = await self.embedding_provider.embed_batch(texts)
                updates = [
                    PageEmbeddingUpdateDTO(page_id=p.page_id, embedding=emb)
                    for p, emb in zip(unembedded, embeddings)
                ]
                await self.repo.update_page_embeddings(updates)
                for p, emb in zip(unembedded, embeddings):
                    p.embedding = emb

            return pages

        # Embeddings are populated: generate query vector and search by vector similarity
        query_vector = await self.embedding_provider.embed_text(query)
        pages = list(
            await self.repo.search_pages_vector(
                doc_id=doc_id, query_vector=query_vector, limit=limit
            )
        )

        # Lazy embedding guarantee for any returned pages
        unembedded = [p for p in pages if p.embedding is None]
        if unembedded:
            texts = [p.markdown_content or p.content for p in unembedded]
            embeddings = await self.embedding_provider.embed_batch(texts)
            updates = [
                PageEmbeddingUpdateDTO(page_id=p.page_id, embedding=emb)
                for p, emb in zip(unembedded, embeddings)
            ]
            await self.repo.update_page_embeddings(updates)
            for p, emb in zip(unembedded, embeddings):
                p.embedding = emb

        return pages

    async def reembed_project_pages(
        self,
        project_id: uuid.UUID,
        batch_size: int = 50,
    ) -> int:
        """
        Use case: batch embedding routine for project pages missing embeddings.
        """
        missing_pages = await self.repo.get_pages_missing_embeddings(
            project_id=project_id,
            batch_size=batch_size,
        )
        if not missing_pages:
            return 0

        texts = [p.markdown_content or p.content for p in missing_pages]
        embeddings = await self.embedding_provider.embed_batch(texts)

        updates: List[PageEmbeddingUpdateDTO] = [
            PageEmbeddingUpdateDTO(page_id=page.page_id, embedding=emb)
            for page, emb in zip(missing_pages, embeddings)
        ]
        await self.repo.update_page_embeddings(updates)
        self.logger.info(
            "Populated missing embeddings for project pages",
            count=len(updates),
            project_id=project_id,
        )
        return len(updates)
