import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions.database import (
    RepositoryError,
    DocumentNotFoundError,
    DuplicateDocumentError,
)
from src.core.interfaces.ilogger import ILogger
from src.models.document import Document
from src.infra.repositories.document_repository import DocumentRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_logger():
    return MagicMock(spec=ILogger)


@pytest.fixture
def doc_repo(mock_session, mock_logger):
    return DocumentRepository(session=mock_session, logger=mock_logger)


@pytest.mark.asyncio
async def test_get_by_id_found(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    expected_doc = Document(doc_id=doc_id, file_path="/path/test.pdf", primary_name="test.pdf")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_doc
    mock_session.execute.return_value = mock_result

    result = await doc_repo.get_by_id(doc_id)
    assert result == expected_doc


@pytest.mark.asyncio
async def test_get_by_id_not_found(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await doc_repo.get_by_id(doc_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_file_hash(doc_repo, mock_session):
    expected_doc = Document(file_hash="abc123hash", file_path="/path/test.pdf")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_doc
    mock_session.execute.return_value = mock_result

    result = await doc_repo.get_by_file_hash("abc123hash")
    assert result == expected_doc


@pytest.mark.asyncio
async def test_create_success(doc_repo, mock_session):
    doc = Document(primary_name="doc.pdf", file_hash="hash1")
    res = await doc_repo.create(doc)
    assert res == doc
    mock_session.add.assert_called_once_with(doc)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(doc)


@pytest.mark.asyncio
async def test_create_duplicate(doc_repo, mock_session):
    doc = Document(primary_name="doc.pdf", file_hash="hash1")
    mock_session.commit.side_effect = IntegrityError("duplicate", orig=None, params={})

    with pytest.raises(DuplicateDocumentError):
        await doc_repo.create(doc)
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_success(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id, primary_name="old.pdf")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = doc
    mock_session.execute.return_value = mock_result

    updated = await doc_repo.update(doc_id, primary_name="new.pdf")
    assert updated.primary_name == "new.pdf"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_not_found(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(DocumentNotFoundError):
        await doc_repo.update(doc_id, primary_name="new.pdf")


@pytest.mark.asyncio
async def test_delete_success(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id, primary_name="test.pdf")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = doc
    mock_session.execute.return_value = mock_result

    res = await doc_repo.delete(doc_id)
    assert res is True
    mock_session.delete.assert_called_once_with(doc)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_document_toc_success(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    toc_data = [{"title": "Intro", "page_num": 1, "level": 1}]
    mock_result = MagicMock()
    mock_result.first.return_value = (toc_data,)
    mock_session.execute.return_value = mock_result

    res = await doc_repo.get_document_toc(doc_id)
    assert res == toc_data


@pytest.mark.asyncio
async def test_get_document_toc_not_found(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(DocumentNotFoundError):
        await doc_repo.get_document_toc(doc_id)


@pytest.mark.asyncio
async def test_get_document_metadata_success(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    meta_data = {"total_pages": 5, "title": "My Doc"}
    mock_result = MagicMock()
    mock_result.first.return_value = (meta_data,)
    mock_session.execute.return_value = mock_result

    res = await doc_repo.get_document_metadata(doc_id)
    assert res == meta_data


@pytest.mark.asyncio
async def test_get_document_metadata_not_found(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(DocumentNotFoundError):
        await doc_repo.get_document_metadata(doc_id)


@pytest.mark.asyncio
async def test_update_toc(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = doc
    mock_session.execute.return_value = mock_result

    toc = [{"title": "Intro", "page_num": 1}]
    updated = await doc_repo.update_toc(doc_id, toc)
    assert updated.toc == toc


@pytest.mark.asyncio
async def test_update_metadata(doc_repo, mock_session):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = doc
    mock_session.execute.return_value = mock_result

    meta = {"total_pages": 10}
    updated = await doc_repo.update_metadata(doc_id, meta)
    assert updated.doc_metadata == meta
