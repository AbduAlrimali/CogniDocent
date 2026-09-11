from typing import AsyncGenerator, Optional
from src.core.interfaces.itts_provider import ITextToSpeechProvider
from src.core.interfaces.ihttp_client import IHTTPClient
from src.core.interfaces.ilogger import ILogger
from src.core.exceptions.http_exceptions import (
    HTTPClientError,
    HTTPConnectionError,
    HTTPTimeoutError,
)
from src.core.exceptions.tts_exceptions import (
    TTSProviderError,
    TTSConnectionError,
    TTSAuthenticationError,
    TTSRateLimitError,
    TTSAudioGenerationError,
    TTSVoiceNotFoundError,
)


class LocalTTS(ITextToSpeechProvider):
    """Text-to-speech provider adapter for self-hosted / local TTS services (e.g. Kokoro, Piper)."""

    def __init__(
        self,
        logger: ILogger,
        http_client: IHTTPClient,
        base_url: str = "http://localhost:8880/v1",
        model: str = "kokoro",
        api_key: Optional[str] = None,
    ):
        self.logger = logger
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def stream_audio(
        self, text: str, voice: str = "alloy"
    ) -> AsyncGenerator[bytes, None]:
        """Streams audio bytes from the local TTS server."""
        if not text or not text.strip():
            return

        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }
        url = f"{self.base_url}/audio/speech"

        self.logger.info("Streaming audio from Local TTS", voice=voice, model=self.model, url=url)

        try:
            async for chunk in self.http_client.stream(
                "POST",
                url,
                payload=payload,
                headers=self.headers,
            ):
                yield chunk

        except HTTPTimeoutError as e:
            self.logger.error("Local TTS request timed out", url=url, exc=e)
            raise TTSConnectionError("LocalTTS", url) from e

        except HTTPConnectionError as e:
            self.logger.error("Local TTS connection failed (ensure local service is running)", url=url, exc=e)
            raise TTSConnectionError("LocalTTS", url) from e

        except HTTPClientError as e:
            msg = str(e).lower()
            self.logger.error("Local TTS client error", error=str(e), exc=e)
            if "401" in msg or "403" in msg or "auth" in msg:
                raise TTSAuthenticationError("LocalTTS") from e
            if "404" in msg or "voice" in msg:
                raise TTSVoiceNotFoundError("LocalTTS", voice) from e
            if "429" in msg or "rate limit" in msg:
                raise TTSRateLimitError("LocalTTS") from e
            raise TTSAudioGenerationError("LocalTTS", str(e)) from e

        except TTSProviderError:
            raise

        except Exception as e:
            self.logger.error("Unexpected error in Local TTS stream", error=str(e), exc=e)
            raise TTSProviderError(f"Unexpected Local TTS error: {str(e)}") from e
