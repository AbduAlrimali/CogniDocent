import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import AIMessageChunk
from langchain_core.language_models.chat_models import BaseChatModel

from src.core.dtos.llm_provider_dtos import DomainMessageDTO, StreamChunkDTO
from src.core.enums import Role
from src.core.interfaces.ilogger import ILogger
from src.infra.llms.base_langchain_adapter import BaseLangChainLLMAdapter


class DummyAdapter(BaseLangChainLLMAdapter):
    pass


@pytest.mark.asyncio
async def test_stream_response_yields_stream_chunk_dto():
    mock_model = MagicMock(spec=BaseChatModel)
    mock_logger = MagicMock(spec=ILogger)

    # Mock astream generator
    async def fake_astream(*args, **kwargs):
        chunk1 = AIMessageChunk(content="Hello ")
        chunk2 = AIMessageChunk(
            content="world!",
            response_metadata={"finish_reason": "stop"}
        )
        yield chunk1
        yield chunk2

    mock_model.astream = fake_astream

    adapter = DummyAdapter(model=mock_model, provider_name="dummy", logger=mock_logger)

    messages = [DomainMessageDTO(role=Role.USER, content="Hi")]
    chunks = []
    async for chunk in adapter.stream_response(messages):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert isinstance(chunks[0], StreamChunkDTO)
    assert chunks[0].content_delta == "Hello "
    assert chunks[0].finish_reason is None

    assert isinstance(chunks[1], StreamChunkDTO)
    assert chunks[1].content_delta == "world!"
    assert chunks[1].finish_reason == "stop"
