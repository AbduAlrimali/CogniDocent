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


class OpenAITTSProvider(ITextToSpeechProvider):
    """Text-to-speech provider implementation using OpenAI's Speech API."""

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        http_client: IHTTPClient,
        base_url: str = "https://api.openai.com/v1",
        model: str = "tts-1",
    ):
        self.api_key = api_key
        self.logger = logger
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def stream_audio(
        self, text: str, voice: str = "alloy"
    ) -> AsyncGenerator[bytes, None]:
        """Streams audio bytes (MP3) generated from text using OpenAI TTS."""
        if not self.api_key or not self.api_key.strip():
            raise TTSAuthenticationError("OpenAI")

        if not text or not text.strip():
            return

        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }
        url = f"{self.base_url}/audio/speech"

        self.logger.info("Streaming audio from OpenAI TTS", voice=voice, model=self.model)

        try:
            async for chunk in self.http_client.stream(
                "POST",
                url,
                payload=payload,
                headers=self.headers,
            ):
                yield chunk

        except HTTPTimeoutError as e:
            self.logger.error("OpenAI TTS request timed out", url=url, exc=e)
            raise TTSConnectionError("OpenAI", url) from e

        except HTTPConnectionError as e:
            self.logger.error("OpenAI TTS connection error", url=url, exc=e)
            raise TTSConnectionError("OpenAI", url) from e

        except HTTPClientError as e:
            msg = str(e).lower()
            self.logger.error("OpenAI TTS client error", error=str(e), exc=e)
            if "401" in msg or "403" in msg or "auth" in msg:
                raise TTSAuthenticationError("OpenAI") from e
            if "404" in msg or "voice" in msg:
                raise TTSVoiceNotFoundError("OpenAI", voice) from e
            if "429" in msg or "rate limit" in msg:
                raise TTSRateLimitError("OpenAI") from e
            raise TTSAudioGenerationError("OpenAI", str(e)) from e

        except TTSProviderError:
            raise

        except Exception as e:
            self.logger.error("Unexpected error in OpenAI TTS stream", error=str(e), exc=e)
            raise TTSProviderError(f"Unexpected OpenAI TTS error: {str(e)}") from e
