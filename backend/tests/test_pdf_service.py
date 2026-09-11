import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.interfaces.ifast_parser import IFastParser
from src.core.interfaces.iembedding_provider import IEmbeddingProvider
from src.core.interfaces.idocument_page_repository import IDocumentPageRepository
from src.core.interfaces.idocument_repository import IDocumentRepository
from src.core.interfaces.ilogger import ILogger
from src.core.dtos.fast_parser_dto import (
    FastParsedDocumentDTO,
    FastPageContentDTO,
    FastDocumentMetadataDTO,
    TOCItemDTO,
)
from src.core.interfaces.ivision_provider import IVisionProvider
from src.core.dtos.llm_provider_dtos import LLMRouteConfigDTO
from src.core.enums import ChatProvider, UploadStatus
from src.core.exceptions.document_exceptions import DocumentNotParsedError
from src.models.document import Document
from src.models.document_page import DocumentPage
from src.services.pdf_service import PDFService
from src.infra.llms.litellm_vision_adapter import LiteLLMVisionProvider


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_parser():
    parser = MagicMock(spec=IFastParser)
    parser.render_page = MagicMock(return_value=b"fake_png_bytes")
    parser.extract_document = MagicMock(
        return_value=FastParsedDocumentDTO(
            metadata=FastDocumentMetadataDTO(total_pages=2, file_size_bytes=100),
            table_of_contents=[],
            pages=[
                FastPageContentDTO(page_num=1, raw_text="Page 1 text", char_count=11, has_images=False, has_tables_hint=False),
                FastPageContentDTO(page_num=2, raw_text="Page 2 text", char_count=11, has_images=True, has_tables_hint=False),
            ],
        )
    )
    return parser


@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=IEmbeddingProvider)
    provider.embed_batch = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
    return provider


@pytest.fixture
def mock_page_repo():
    repo = AsyncMock(spec=IDocumentPageRepository)
    repo.bulk_create = AsyncMock(side_effect=lambda pages: pages)
    repo.get_pages_in_range = AsyncMock(return_value=[])
    repo.search_pages_vector = AsyncMock(return_value=[])
    repo.get_fallback_pages = AsyncMock(return_value=[])
    repo.update_pages = AsyncMock()
    return repo


@pytest.fixture
def mock_doc_repo():
    repo = AsyncMock(spec=IDocumentRepository)
    repo.get_document_toc = AsyncMock(return_value=None)
    repo.get_document_metadata = AsyncMock(return_value=None)
    repo.update_toc = AsyncMock()
    repo.update_metadata = AsyncMock()
    repo.update = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_logger():
    return MagicMock(spec=ILogger)


@pytest.fixture
def mock_vision_llm():
    vision = AsyncMock(spec=IVisionProvider)
    vision.extract_markdown = AsyncMock(return_value="# Extracted Markdown")
    return vision


@pytest.fixture
def pdf_service(
    mock_session,
    mock_parser,
    mock_provider,
    mock_page_repo,
    mock_logger,
    mock_doc_repo,
    mock_vision_llm,
):
    return PDFService(
        session=mock_session,
        parser=mock_parser,
        embedding_provider=mock_provider,
        page_repo=mock_page_repo,
        logger=mock_logger,
        doc_repo=mock_doc_repo,
        vision_llm=mock_vision_llm,
    )


@pytest.mark.asyncio
async def test_pdf_service_render_page_success(pdf_service, mock_session, mock_parser):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "/tmp/sample.pdf"
    mock_session.execute.return_value = mock_result

    image_bytes = await pdf_service.render_page(doc_id=doc_id, page_num=1)

    assert image_bytes == b"fake_png_bytes"
    mock_parser.render_page.assert_called_once_with("/tmp/sample.pdf", 1)


@pytest.mark.asyncio
async def test_pdf_service_render_page_not_found(pdf_service, mock_session):
    doc_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(FileNotFoundError, match=f"Document {doc_id} not found"):
        await pdf_service.render_page(doc_id=doc_id, page_num=1)


@pytest.mark.asyncio
async def test_pdf_service_parse_and_embed_document(
    pdf_service, mock_session, mock_parser, mock_provider, mock_page_repo
):
    doc_id = uuid.uuid4()
    doc = Document(
        doc_id=doc_id,
        file_path="/tmp/sample.pdf",
        file_size_bytes=100,
        file_hash="hash123",
        content_type="application/pdf",
        status=UploadStatus.COMPLETED,
        primary_name="sample.pdf",
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = doc
    mock_session.execute.return_value = mock_result

    pages = await pdf_service.parse_and_embed_document(doc_id=doc_id)

    assert len(pages) == 2
    mock_provider.embed_batch.assert_called_once_with(["Page 1 text", "Page 2 text"])
    mock_page_repo.bulk_create.assert_called_once()
    
    assert pages[0].doc_id == doc_id
    assert pages[0].page_num == 1
    assert pages[0].content == "Page 1 text"
    assert pages[0].content_vector == [0.1, 0.2]
    assert pages[0].deep_content is None
    assert pages[0].deep_content_vector is None

    assert pages[1].doc_id == doc_id
    assert pages[1].page_num == 2
    assert pages[1].content == "Page 2 text"
    assert pages[1].content_vector == [0.3, 0.4]


@pytest.mark.asyncio
async def test_litellm_vision_provider_extract_markdown():
    config = LLMRouteConfigDTO(
        provider=ChatProvider.OPENAI,
        model_name="gpt-4o",
        temperature=0.0,
    )
    provider = LiteLLMVisionProvider(config=config)

    fake_response = MagicMock()
    fake_choice = MagicMock()
    fake_choice.message.content = "# Page Header\nPage content."
    fake_response.choices = [fake_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = fake_response

        markdown = await provider.extract_markdown(b"fake_image_bytes")

        assert markdown == "# Page Header\nPage content."
        mock_acompletion.assert_called_once()
        call_kwargs = mock_acompletion.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["temperature"] == 0.0
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert "reading order" in messages[0]["content"]
        assert "images, figures, charts, diagrams" in messages[0]["content"]


def test_pymupdf_parser_render_page():
    from src.infra.pymupdf_parser import PyMuPDFParser

    mock_mupdf = MagicMock()
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_pix = MagicMock()
    mock_pix.tobytes.return_value = b"fake_rendered_png"
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.__len__.return_value = 3
    mock_doc.__getitem__.return_value = mock_page
    mock_doc.needs_pass = False
    mock_mupdf.open.return_value = mock_doc

    logger = MagicMock()
    parser = PyMuPDFParser(mupdf_client=mock_mupdf, logger=logger)
    with patch("pathlib.Path.exists", return_value=True):
        result = parser.render_page("/fake/path.pdf", page_num=2, dpi=150)
        assert result == b"fake_rendered_png"
        mock_page.get_pixmap.assert_called_once_with(dpi=150)
        mock_doc.close.assert_called_once()


@pytest.mark.asyncio
async def test_pdf_service_get_document_toc_cached(pdf_service, mock_doc_repo, mock_parser):
    doc_id = uuid.uuid4()
    mock_doc_repo.get_document_toc.return_value = [
        {"title": "Chapter 1", "page_num": 1, "level": 1}
    ]

    toc = await pdf_service.get_document_toc(doc_id)

    assert len(toc) == 1
    assert toc[0].title == "Chapter 1"
    assert toc[0].page_num == 1
    assert toc[0].level == 1
    mock_parser.extract_table_of_contents.assert_not_called()


@pytest.mark.asyncio
async def test_pdf_service_get_document_toc_extracted(pdf_service, mock_doc_repo, mock_parser):
    doc_id = uuid.uuid4()
    mock_doc_repo.get_document_toc.return_value = None
    mock_doc_repo.get_by_id.return_value = Document(doc_id=doc_id, file_path="/tmp/test.pdf")

    mock_parser.extract_table_of_contents = MagicMock(
        return_value=[TOCItemDTO(title="Introduction", page_num=1, level=1)]
    )

    toc = await pdf_service.get_document_toc(doc_id)

    assert len(toc) == 1
    assert toc[0].title == "Introduction"
    mock_parser.extract_table_of_contents.assert_called_once_with("/tmp/test.pdf")
    mock_doc_repo.update_toc.assert_called_once_with(
        doc_id, [{"title": "Introduction", "page_num": 1, "level": 1}]
    )


@pytest.mark.asyncio
async def test_pdf_service_get_document_metadata_cached(pdf_service, mock_doc_repo, mock_parser):
    doc_id = uuid.uuid4()
    mock_doc_repo.get_document_metadata.return_value = {
        "total_pages": 42,
        "file_size_bytes": 1024,
        "title": "Quantum Computing",
        "author": "Alice",
        "creator": "LaTeX",
        "producer": "pdfTeX",
        "custom_metadata": {"subject": "Physics"},
    }

    meta = await pdf_service.get_document_metadata(doc_id)

    assert meta.total_pages == 42
    assert meta.title == "Quantum Computing"
    assert meta.author == "Alice"
    mock_parser.extract_metadata.assert_not_called()


@pytest.mark.asyncio
async def test_pdf_service_get_document_metadata_extracted(pdf_service, mock_doc_repo, mock_parser):
    doc_id = uuid.uuid4()
    mock_doc_repo.get_document_metadata.return_value = None
    mock_doc_repo.get_by_id.return_value = Document(doc_id=doc_id, file_path="/tmp/test.pdf")

    mock_parser.extract_metadata = MagicMock(
        return_value=FastDocumentMetadataDTO(
            total_pages=15,
            file_size_bytes=2048,
            title="Extracted Title",
            author="Bob",
            creator=None,
            producer=None,
        )
    )

    meta = await pdf_service.get_document_metadata(doc_id)

    assert meta.total_pages == 15
    assert meta.title == "Extracted Title"
    mock_parser.extract_metadata.assert_called_once_with("/tmp/test.pdf")
    mock_doc_repo.update_metadata.assert_called_once_with(
        doc_id,
        {
            "total_pages": 15,
            "file_size_bytes": 2048,
            "title": "Extracted Title",
            "author": "Bob",
            "creator": None,
            "producer": None,
            "custom_metadata": {},
        },
    )


@pytest.mark.asyncio
async def test_pdf_service_get_document_toc_not_found(pdf_service, mock_doc_repo, mock_session):
    doc_id = uuid.uuid4()
    mock_doc_repo.get_document_toc.return_value = None
    mock_doc_repo.get_by_id.return_value = None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(FileNotFoundError, match=f"Document {doc_id} not found"):
        await pdf_service.get_document_toc(doc_id)


@pytest.mark.asyncio
async def test_pdf_service_get_pages_in_range_success(pdf_service, mock_doc_repo, mock_page_repo):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id, status=UploadStatus.COMPLETED)
    mock_doc_repo.get_by_id.return_value = doc

    page1 = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=1, content="Page 1")
    page2 = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=2, content="Page 2")
    mock_page_repo.get_pages_in_range.return_value = [page1, page2]

    pages = await pdf_service.get_pages_in_range(doc_id, start_page=1, end_page=2)

    assert len(pages) == 2
    assert pages[0].content == "Page 1"
    assert pages[1].content == "Page 2"
    mock_page_repo.get_pages_in_range.assert_called_once_with(doc_id, 1, 2)


@pytest.mark.asyncio
async def test_pdf_service_get_pages_in_range_empty(pdf_service, mock_doc_repo, mock_page_repo):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id, status=UploadStatus.COMPLETED)
    mock_doc_repo.get_by_id.return_value = doc
    mock_page_repo.get_pages_in_range.return_value = []

    pages = await pdf_service.get_pages_in_range(doc_id, start_page=10, end_page=20)

    assert pages == []
    mock_page_repo.get_pages_in_range.assert_called_once_with(doc_id, 10, 20)


@pytest.mark.asyncio
async def test_pdf_service_get_pages_in_range_not_parsed(pdf_service, mock_doc_repo):
    doc_id = uuid.uuid4()
    doc = Document(doc_id=doc_id, status=UploadStatus.PROCESSING)
    mock_doc_repo.get_by_id.return_value = doc

    with pytest.raises(DocumentNotParsedError):
        await pdf_service.get_pages_in_range(doc_id, start_page=1, end_page=5)


@pytest.mark.asyncio
async def test_pdf_service_get_pages_in_range_not_found(pdf_service, mock_doc_repo, mock_session):
    doc_id = uuid.uuid4()
    mock_doc_repo.get_by_id.return_value = None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(FileNotFoundError, match=f"Document {doc_id} not found"):
        await pdf_service.get_pages_in_range(doc_id, start_page=1, end_page=5)


@pytest.mark.asyncio
async def test_pdf_service_hybrid_retrieve_unparsed_pages(
    pdf_service, mock_page_repo, mock_provider, mock_parser, mock_vision_llm
):
    doc_id = uuid.uuid4()
    page1 = DocumentPage(
        page_id=uuid.uuid4(),
        doc_id=doc_id,
        page_num=1,
        content="Raw text 1",
        content_vector=[0.1, 0.2, 0.3],
        deep_content=None,
        deep_content_vector=None,
    )
    mock_page_repo.search_pages_vector.return_value = [page1]

    with patch.object(pdf_service, "render_page", new=AsyncMock(return_value=b"fake_bytes")):
        pages = await pdf_service.hybrid_retrieve(doc_id=doc_id, query="quantum", limit=3)

    assert len(pages) == 1
    mock_provider.embed_text.assert_called_once_with("quantum")
    mock_page_repo.search_pages_vector.assert_called_once()
    mock_vision_llm.extract_markdown.assert_called_once_with(b"fake_bytes")
    mock_provider.embed_batch.assert_called_once_with(["# Extracted Markdown"])
    mock_page_repo.update_pages.assert_called_once()
    assert page1.deep_content == "# Extracted Markdown"


@pytest.mark.asyncio
async def test_pdf_service_hybrid_retrieve_already_parsed(
    pdf_service, mock_page_repo, mock_provider, mock_vision_llm
):
    doc_id = uuid.uuid4()
    page1 = DocumentPage(
        page_id=uuid.uuid4(),
        doc_id=doc_id,
        page_num=1,
        content="Raw text 1",
        content_vector=[0.1, 0.2, 0.3],
        deep_content="# Existing Deep Markdown",
        deep_content_vector=[0.1, 0.2, 0.3],
    )
    mock_page_repo.search_pages_vector.return_value = [page1]

    pages = await pdf_service.hybrid_retrieve(doc_id=doc_id, query="quantum", limit=3)

    assert len(pages) == 1
    mock_provider.embed_text.assert_called_once_with("quantum")
    mock_vision_llm.extract_markdown.assert_not_called()
    mock_page_repo.update_pages.assert_not_called()


@pytest.mark.asyncio
async def test_pdf_service_hybrid_retrieve_fallback(
    pdf_service, mock_page_repo, mock_provider, mock_vision_llm
):
    doc_id = uuid.uuid4()
    fallback_page = DocumentPage(
        page_id=uuid.uuid4(),
        doc_id=doc_id,
        page_num=1,
        content="Fallback text",
        content_vector=None,
        deep_content=None,
        deep_content_vector=None,
    )
    mock_page_repo.search_pages_vector.return_value = []
    mock_page_repo.get_fallback_pages.return_value = [fallback_page]

    with patch.object(pdf_service, "render_page", new=AsyncMock(return_value=b"fake_bytes")):
        pages = await pdf_service.hybrid_retrieve(doc_id=doc_id, query="quantum", limit=3)

    assert len(pages) == 1
    mock_page_repo.get_fallback_pages.assert_called_once_with(doc_id=doc_id, limit=3)
    mock_vision_llm.extract_markdown.assert_called_once()
    assert fallback_page.deep_content == "# Extracted Markdown"


