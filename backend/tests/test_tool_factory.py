import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.pdf_service import PDFService
from src.models.document_page import DocumentPage
from src.core.dtos.fast_parser_dto import TOCItemDTO, FastDocumentMetadataDTO
from src.infra.orchestrators.langgraph.tools.tool_factory import LangGraphToolFactory


@pytest.fixture
def mock_pdf_service():
    service = AsyncMock(spec=PDFService)
    service.hybrid_retrieve = AsyncMock()
    service.get_pages_in_range = AsyncMock()
    service.get_document_toc = AsyncMock()
    service.get_document_metadata = AsyncMock()
    return service


@pytest.fixture
def tool_factory(mock_pdf_service):
    return LangGraphToolFactory(pdf_service=mock_pdf_service)


def test_get_all_tools(tool_factory):
    tools = tool_factory.get_all_tools()
    assert len(tools) == 4
    tool_names = [t.name for t in tools]
    assert "search_documents" in tool_names
    assert "get_pages_in_range" in tool_names
    assert "get_document_toc" in tool_names
    assert "get_document_metadata" in tool_names


@pytest.mark.asyncio
async def test_search_documents_tool(tool_factory, mock_pdf_service):
    tools = {t.name: t for t in tool_factory.get_all_tools()}
    doc_id = uuid.uuid4()
    page = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=1, content="Hello World")
    mock_pdf_service.hybrid_retrieve.return_value = [page]

    search_tool = tools["search_documents"]
    result = await search_tool.ainvoke({"query": "greeting", "state": {"document_id": doc_id}})

    assert "--- Page 1 ---" in result
    assert "Hello World" in result
    mock_pdf_service.hybrid_retrieve.assert_called_once_with(doc_id=doc_id, query="greeting", limit=3)


@pytest.mark.asyncio
async def test_get_pages_in_range_tool(tool_factory, mock_pdf_service):
    tools = {t.name: t for t in tool_factory.get_all_tools()}
    doc_id = uuid.uuid4()
    page = DocumentPage(page_id=uuid.uuid4(), doc_id=doc_id, page_num=2, content="Page 2 text")
    mock_pdf_service.get_pages_in_range.return_value = [page]

    range_tool = tools["get_pages_in_range"]
    result = await range_tool.ainvoke({"start_page": 2, "end_page": 2, "state": {"document_id": doc_id}})

    assert "--- Page 2 ---" in result
    assert "Page 2 text" in result
    mock_pdf_service.get_pages_in_range.assert_called_once_with(doc_id=doc_id, start_page=2, end_page=2)


@pytest.mark.asyncio
async def test_get_document_toc_tool(tool_factory, mock_pdf_service):
    tools = {t.name: t for t in tool_factory.get_all_tools()}
    doc_id = uuid.uuid4()
    mock_pdf_service.get_document_toc.return_value = [
        TOCItemDTO(title="Introduction", page_num=1, level=1),
        TOCItemDTO(title="Deep Dive", page_num=5, level=2),
    ]

    toc_tool = tools["get_document_toc"]
    result = await toc_tool.ainvoke({"state": {"document_id": doc_id}})

    assert "- Introduction (Page 1)" in result
    assert "-   Deep Dive (Page 5)" in result
    mock_pdf_service.get_document_toc.assert_called_once_with(doc_id=doc_id)


@pytest.mark.asyncio
async def test_get_document_metadata_tool(tool_factory, mock_pdf_service):
    tools = {t.name: t for t in tool_factory.get_all_tools()}
    doc_id = uuid.uuid4()
    mock_pdf_service.get_document_metadata.return_value = FastDocumentMetadataDTO(
        total_pages=20,
        file_size_bytes=5000,
        title="Sample Book",
        author="John Doe",
    )

    meta_tool = tools["get_document_metadata"]
    result = await meta_tool.ainvoke({"state": {"document_id": doc_id}})

    assert "Title: Sample Book" in result
    assert "Author: John Doe" in result
    assert "Total Pages: 20" in result
    mock_pdf_service.get_document_metadata.assert_called_once_with(doc_id=doc_id)
