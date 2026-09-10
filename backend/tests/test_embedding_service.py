import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.dtos.llm_provider_dtos import EmbeddingConfigDTO
from src.core.enums import EmbeddingProvider
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.core.interfaces.ilogger import ILogger
from src.models.document_page import DocumentPage
from src.schemas.document_page import DocumentPageResponse
from src.services.embedding_service import EmbeddingService


@pytest.fixture
def mock_repo():
    repo = AsyncMock(spec=IDocumentPageRepository)
    repo.get_embedding_metadata = AsyncMock()
    repo.alter_embedding_dimensions = AsyncMock()
    repo.nullify_project_embeddings = AsyncMock()
    repo.upsert_embedding_metadata = AsyncMock()
    repo.count_populated_embeddings = AsyncMock()
    repo.search_pages_fts = AsyncMock()
    repo.search_pages_vector = AsyncMock()
    repo.get_fallback_pages = AsyncMock()
    repo.get_pages_missing_embeddings = AsyncMock()
    repo.update_page_embeddings = AsyncMock()
    return repo


@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=IEmbeddingProvider)
    provider.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])
    provider.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return provider


@pytest.fixture
def mock_logger():
    return MagicMock(spec=ILogger)


@pytest.fixture
def service(mock_repo, mock_provider, mock_logger):
    return EmbeddingService(
        document_page_repo=mock_repo,
        embedding_provider=mock_provider,
        logger=mock_logger,
    )


@pytest.mark.asyncio
async def test_update_project_embedding_model_dimension_change(service, mock_repo):
    project_id = uuid.uuid4()
    mock_repo.get_embedding_metadata.return_value = ("nomic-embed-text-v2-moe", 768)

    new_config = EmbeddingConfigDTO(
        provider=EmbeddingProvider.OPENAI,
        model_name="text-embedding-3-small",
        dimensions=1536,
    )

    await service.update_project_embedding_model(project_id, new_config)

    # Verifies service decided to alter dimensions via DDL and upsert metadata
    mock_repo.alter_embedding_dimensions.assert_called_once_with(1536)
    mock_repo.nullify_project_embeddings.assert_not_called()
    mock_repo.upsert_embedding_metadata.assert_called_once_with(
        project_id=project_id,
        active_model="text-embedding-3-small",
        dimensions=1536,
    )


@pytest.mark.asyncio
async def test_update_project_embedding_model_same_dimension_different_model(service, mock_repo):
    project_id = uuid.uuid4()
    mock_repo.get_embedding_metadata.return_value = ("nomic-embed-text-v2-moe", 768)

    new_config = EmbeddingConfigDTO(
        provider=EmbeddingProvider.OLLAMA,
        model_name="bge-base-en-v1.5",
        dimensions=768,
    )

    await service.update_project_embedding_model(project_id, new_config)

    # Verifies service decided to nullify project embeddings and upsert metadata
    mock_repo.alter_embedding_dimensions.assert_not_called()
    mock_repo.nullify_project_embeddings.assert_called_once_with(project_id)
    mock_repo.upsert_embedding_metadata.assert_called_once_with(
        project_id=project_id,
        active_model="bge-base-en-v1.5",
        dimensions=768,
    )


@pytest.mark.asyncio
async def test_update_project_embedding_model_skip_when_same(service, mock_repo):
    project_id = uuid.uuid4()
    mock_repo.get_embedding_metadata.return_value = ("nomic-embed-text-v2-moe", 768)

    same_config = EmbeddingConfigDTO(
        provider=EmbeddingProvider.OLLAMA,
        model_name="nomic-embed-text-v2-moe",
        dimensions=768,
    )

    await service.update_project_embedding_model(project_id, same_config)

    mock_repo.alter_embedding_dimensions.assert_not_called()
    mock_repo.nullify_project_embeddings.assert_not_called()
    mock_repo.upsert_embedding_metadata.assert_not_called()


@pytest.mark.asyncio
async def test_hybrid_retrieve_fallback_unpopulated(service, mock_repo, mock_provider):
    doc_id = uuid.uuid4()
    mock_repo.count_populated_embeddings.return_value = 0

    page1 = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=1, content="Content 1", embedding=None)
    page2 = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=2, content="Content 2", embedding=None)
    mock_repo.search_pages_fts.return_value = [page1, page2]

    pages = await service.hybrid_retrieve(doc_id=doc_id, query="quantum", limit=3)

    # Service orchestrates FTS fallback + lazy embedding generation
    assert len(pages) == 2
    mock_repo.search_pages_fts.assert_called_once_with(doc_id=doc_id, query="quantum", limit=3)
    mock_provider.embed_batch.assert_called_once_with(["Content 1", "Content 2"])
    assert mock_repo.update_page_embeddings.called
    assert page1.embedding == [0.1, 0.2, 0.3]
    assert page2.embedding == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_hybrid_retrieve_vector_search_when_populated(service, mock_repo, mock_provider):
    doc_id = uuid.uuid4()
    mock_repo.count_populated_embeddings.return_value = 5

    page1 = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=1, content="Content 1", embedding=[0.1, 0.2, 0.3])
    mock_repo.search_pages_vector.return_value = [page1]

    pages = await service.hybrid_retrieve(doc_id=doc_id, query="quantum", limit=3)

    assert len(pages) == 1
    mock_provider.embed_text.assert_called_once_with("quantum")
    mock_repo.search_pages_vector.assert_called_once_with(doc_id=doc_id, query_vector=[0.1, 0.2, 0.3], limit=3)


@pytest.mark.asyncio
async def test_reembed_project_pages(service, mock_repo, mock_provider):
    project_id = uuid.uuid4()
    page_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    mock_page = DocumentPageResponse(
        page_id=page_id,
        doc_id=doc_id,
        page_num=1,
        content="Test page content",
        embedding=None,
    )
    mock_repo.get_pages_missing_embeddings.return_value = [mock_page]

    count = await service.reembed_project_pages(project_id=project_id, batch_size=10)

    assert count == 1
    mock_provider.embed_batch.assert_called_once_with(["Test page content"])
    from src.core.dtos.embedding_dtos import PageEmbeddingUpdateDTO
    mock_repo.update_page_embeddings.assert_called_once_with(
        [PageEmbeddingUpdateDTO(page_id=page_id, embedding=[0.1, 0.2, 0.3])]
    )
