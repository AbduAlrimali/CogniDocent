import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.dtos.llm_provider_dtos import DomainMessageDTO, LLMResponseDTO
from src.core.enums import Role
from src.core.prompts import AUDIO_SCRIPT_PROMPT_TEMPLATE
from src.services.audio_explanation_service import AudioExplanationService


class FakePage:
    def __init__(self, page_number: int, content: str = "", deep_content: str = None):
        self.page_number = page_number
        self.content = content
        self.deep_content = deep_content


@pytest.fixture
def mock_pdf_service():
    service = MagicMock()
    service.get_pages_in_range = AsyncMock()
    return service


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate_response = AsyncMock()
    return llm


@pytest.fixture
def mock_tts():
    tts = MagicMock()
    async def fake_stream_audio(text, voice="alloy"):
        yield b"chunk_1"
        yield b"chunk_2"
    tts.stream_audio = fake_stream_audio
    return tts


class TestAudioExplanationService:
    @pytest.mark.asyncio
    async def test_explain_page_audio_success(self, mock_pdf_service, mock_llm, mock_tts):
        doc_id = uuid.uuid4()
        fake_page = FakePage(page_number=1, content="Basic page content", deep_content="Detailed parsed content")
        mock_pdf_service.get_pages_in_range.return_value = [fake_page]

        mock_llm.generate_response.return_value = LLMResponseDTO(
            message=DomainMessageDTO(role=Role.ASSISTANT, content="Spoken explanation of page 1"),
            finish_reason="stop",
        )

        service = AudioExplanationService(
            pdf_service=mock_pdf_service,
            llm_provider=mock_llm,
            tts_provider=mock_tts,
        )

        chunks = [c async for c in service.explain_page_audio(doc_id=doc_id, page_num=1, voice="echo")]
        assert chunks == [b"chunk_1", b"chunk_2"]

        # Verify PDF service called with page_num
        mock_pdf_service.get_pages_in_range.assert_awaited_once_with(doc_id, start_page=1, end_page=1)

        # Verify LLM called via generate_response interface
        assert mock_llm.generate_response.await_count == 1
        call_args = mock_llm.generate_response.await_args
        messages = call_args.kwargs.get("messages") or call_args.args[0]
        assert len(messages) == 1
        assert messages[0].role == Role.USER
        assert "Detailed parsed content" in messages[0].content

    @pytest.mark.asyncio
    async def test_explain_page_audio_custom_prompt_injection(self, mock_pdf_service, mock_llm, mock_tts):
        doc_id = uuid.uuid4()
        fake_page = FakePage(page_number=2, content="Page 2 raw text")
        mock_pdf_service.get_pages_in_range.return_value = [fake_page]

        custom_prompt = "Custom system prompt: {page_content}"
        mock_llm.generate_response.return_value = LLMResponseDTO(
            message=DomainMessageDTO(role=Role.ASSISTANT, content="Custom script"),
            finish_reason="stop",
        )

        service = AudioExplanationService(
            pdf_service=mock_pdf_service,
            llm_provider=mock_llm,
            tts_provider=mock_tts,
            script_prompt_template=custom_prompt,
        )

        chunks = [c async for c in service.explain_page_audio(doc_id=doc_id, page_num=2)]
        assert chunks == [b"chunk_1", b"chunk_2"]

        call_args = mock_llm.generate_response.await_args
        messages = call_args.kwargs.get("messages") or call_args.args[0]
        assert messages[0].content == "Custom system prompt: Page 2 raw text"

    @pytest.mark.asyncio
    async def test_explain_page_audio_not_found(self, mock_pdf_service, mock_llm, mock_tts):
        doc_id = uuid.uuid4()
        mock_pdf_service.get_pages_in_range.return_value = []

        service = AudioExplanationService(
            pdf_service=mock_pdf_service,
            llm_provider=mock_llm,
            tts_provider=mock_tts,
        )

        with pytest.raises(FileNotFoundError, match="Page 5 not found"):
            async for _ in service.explain_page_audio(doc_id=doc_id, page_num=5):
                pass
