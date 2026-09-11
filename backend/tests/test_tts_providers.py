import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.exceptions.http_exceptions import (
    HTTPClientError,
    HTTPConnectionError,
    HTTPTimeoutError,
)
from src.core.exceptions.tts_exceptions import (
    TTSAuthenticationError,
    TTSConnectionError,
    TTSRateLimitError,
    TTSAudioGenerationError,
    TTSVoiceNotFoundError,
    TTSProviderError,
)
from src.infra.tts.openai_tts_provider import OpenAITTSProvider
from src.infra.tts.elevenlabs_tts_adapter import ElevenLabsTTSAdapter
from src.infra.tts.local_tts_provider import LocalTTS


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_http_client():
    return MagicMock()


class TestOpenAITTSProvider:
    @pytest.mark.asyncio
    async def test_stream_audio_success(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            yield b"chunk1"
            yield b"chunk2"

        mock_http_client.stream = fake_stream

        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        chunks = []
        async for chunk in provider.stream_audio("Hello world", voice="nova"):
            chunks.append(chunk)

        assert chunks == [b"chunk1", b"chunk2"]

    @pytest.mark.asyncio
    async def test_empty_api_key_raises_auth_error(self, mock_logger, mock_http_client):
        provider = OpenAITTSProvider(
            api_key="",
            logger=mock_logger,
            http_client=mock_http_client,
        )
        with pytest.raises(TTSAuthenticationError):
            async for _ in provider.stream_audio("Hello world"):
                pass

    @pytest.mark.asyncio
    async def test_empty_text_returns_nothing(self, mock_logger, mock_http_client):
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )
        chunks = [c async for c in provider.stream_audio("   ")]
        assert chunks == []

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPTimeoutError("timed out")
            yield b""

        mock_http_client.stream = fake_stream
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSConnectionError):
            async for _ in provider.stream_audio("test"):
                pass

    @pytest.mark.asyncio
    async def test_connection_failure_raises_connection_error(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPConnectionError("failed")
            yield b""

        mock_http_client.stream = fake_stream
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSConnectionError):
            async for _ in provider.stream_audio("test"):
                pass

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPClientError("401 Unauthorized")
            yield b""

        mock_http_client.stream = fake_stream
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSAuthenticationError):
            async for _ in provider.stream_audio("test"):
                pass

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPClientError("429 rate limit exceeded")
            yield b""

        mock_http_client.stream = fake_stream
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSRateLimitError):
            async for _ in provider.stream_audio("test"):
                pass

    @pytest.mark.asyncio
    async def test_404_raises_voice_not_found(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPClientError("404 voice not found")
            yield b""

        mock_http_client.stream = fake_stream
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSVoiceNotFoundError):
            async for _ in provider.stream_audio("test", voice="invalid"):
                pass

    @pytest.mark.asyncio
    async def test_500_raises_audio_generation_error(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPClientError("500 internal server error")
            yield b""

        mock_http_client.stream = fake_stream
        provider = OpenAITTSProvider(
            api_key="sk-test",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSAudioGenerationError):
            async for _ in provider.stream_audio("test"):
                pass


class TestElevenLabsTTSAdapter:
    @pytest.mark.asyncio
    async def test_stream_audio_success(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            yield b"eleven1"
            yield b"eleven2"

        mock_http_client.stream = fake_stream
        adapter = ElevenLabsTTSAdapter(
            api_key="xi-test-key",
            logger=mock_logger,
            http_client=mock_http_client,
        )

        chunks = [c async for c in adapter.stream_audio("Hello", voice="alloy")]
        assert chunks == [b"eleven1", b"eleven2"]

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_auth(self, mock_logger, mock_http_client):
        adapter = ElevenLabsTTSAdapter(
            api_key="",
            logger=mock_logger,
            http_client=mock_http_client,
        )
        with pytest.raises(TTSAuthenticationError):
            async for _ in adapter.stream_audio("Hello"):
                pass

    @pytest.mark.asyncio
    async def test_404_raises_voice_not_found(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPClientError("404 voice_id not found")
            yield b""

        mock_http_client.stream = fake_stream
        adapter = ElevenLabsTTSAdapter(
            api_key="xi-key",
            logger=mock_logger,
            http_client=mock_http_client,
        )
        with pytest.raises(TTSVoiceNotFoundError):
            async for _ in adapter.stream_audio("Hello", voice="unknown_voice_id"):
                pass


class TestLocalTTS:
    @pytest.mark.asyncio
    async def test_stream_audio_success(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            yield b"local_chunk"

        mock_http_client.stream = fake_stream
        adapter = LocalTTS(
            logger=mock_logger,
            http_client=mock_http_client,
        )

        chunks = [c async for c in adapter.stream_audio("Testing local")]
        assert chunks == [b"local_chunk"]

    @pytest.mark.asyncio
    async def test_connection_error(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPConnectionError("connection refused")
            yield b""

        mock_http_client.stream = fake_stream
        adapter = LocalTTS(
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSConnectionError):
            async for _ in adapter.stream_audio("Testing"):
                pass

    @pytest.mark.asyncio
    async def test_voice_not_found(self, mock_logger, mock_http_client):
        async def fake_stream(*args, **kwargs):
            raise HTTPClientError("404 Voice not found")
            yield b""

        mock_http_client.stream = fake_stream
        adapter = LocalTTS(
            logger=mock_logger,
            http_client=mock_http_client,
        )

        with pytest.raises(TTSVoiceNotFoundError):
            async for _ in adapter.stream_audio("Testing", voice="nonexistent"):
                pass
