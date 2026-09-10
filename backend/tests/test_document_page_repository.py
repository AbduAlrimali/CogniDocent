import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.ilogger import ILogger
from src.infra.repositories.document_page_repository import DocumentPageRepository
from src.models.document_page import DocumentPage
from src.models.embedding_index_metadata import EmbeddingIndexMetadata


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_logger():
    return MagicMock(spec=ILogger)


@pytest.fixture
def repo(mock_session, mock_logger):
    return DocumentPageRepository(session=mock_session, logger=mock_logger)


@pytest.mark.asyncio
async def test_get_embedding_metadata(repo, mock_session):
    project_id = uuid.uuid4()
    mock_record = EmbeddingIndexMetadata(
        project_id=project_id,
        active_model="nomic-embed-text-v2-moe",
        dimensions=768,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_record
    mock_session.execute.return_value = mock_result

    metadata = await repo.get_embedding_metadata(project_id)
    assert metadata == ("nomic-embed-text-v2-moe", 768)


@pytest.mark.asyncio
async def test_upsert_embedding_metadata_update_existing(repo, mock_session):
    project_id = uuid.uuid4()
    existing = EmbeddingIndexMetadata(
        project_id=project_id,
        active_model="old-model",
        dimensions=768,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_session.execute.return_value = mock_result

    await repo.upsert_embedding_metadata(project_id, "new-model", 1536)
    assert existing.active_model == "new-model"
    assert existing.dimensions == 1536
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_alter_embedding_dimensions(repo, mock_session):
    await repo.alter_embedding_dimensions(1536)
    executed_sqls = [
        str(call.args[0]) for call in mock_session.execute.call_args_list if len(call.args) > 0
    ]
    assert any("DROP INDEX IF EXISTS idx_document_pages_embedding" in sql for sql in executed_sqls)
    assert any("ALTER TABLE document_pages ALTER COLUMN embedding TYPE vector(1536) USING NULL" in sql for sql in executed_sqls)
    assert any("CREATE INDEX idx_document_pages_embedding ON document_pages USING hnsw" in sql for sql in executed_sqls)
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_nullify_project_embeddings(repo, mock_session):
    project_id = uuid.uuid4()
    await repo.nullify_project_embeddings(project_id)
    assert mock_session.execute.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_count_populated_embeddings(repo, mock_session):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5
    mock_session.execute.return_value = mock_result

    count = await repo.count_populated_embeddings(doc_id)
    assert count == 5


@pytest.mark.asyncio
async def test_search_pages_fts(repo, mock_session):
    doc_id = uuid.uuid4()
    page = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=1, content="test")
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [page]
    mock_session.execute.return_value = mock_result

    pages = await repo.search_pages_fts(doc_id=doc_id, query="test query", limit=3)
    assert len(pages) == 1
    assert pages[0] == page


@pytest.mark.asyncio
async def test_search_pages_vector(repo, mock_session):
    doc_id = uuid.uuid4()
    page = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=1, content="test", embedding=[0.1, 0.2])
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [page]
    mock_session.execute.return_value = mock_result

    pages = await repo.search_pages_vector(doc_id=doc_id, query_vector=[0.1, 0.2], limit=3)
    assert len(pages) == 1
    assert pages[0] == page


from src.core.dtos.embedding_dtos import PageEmbeddingUpdateDTO

@pytest.mark.asyncio
async def test_update_page_embeddings(repo, mock_session):
    page_id = uuid.uuid4()
    await repo.update_page_embeddings([PageEmbeddingUpdateDTO(page_id=page_id, embedding=[0.1, 0.2])])
    assert mock_session.execute.called
    assert mock_session.commit.called
