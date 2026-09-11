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


class ElevenLabsTTSAdapter(ITextToSpeechProvider):
    """Text-to-speech provider adapter using ElevenLabs API."""

    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    def __init__(
        self,
        api_key: str,
        logger: ILogger,
        http_client: IHTTPClient,
        base_url: str = "https://api.elevenlabs.io/v1",
        model_id: str = "eleven_monolingual_v1",
        default_voice_id: Optional[str] = None,
    ):
        self.api_key = api_key
        self.logger = logger
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.default_voice_id = default_voice_id or self.DEFAULT_VOICE_ID
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def stream_audio(
        self, text: str, voice: str = "alloy"
    ) -> AsyncGenerator[bytes, None]:
        """Streams audio bytes (MP3) generated from text using ElevenLabs TTS."""
        if not self.api_key or not self.api_key.strip():
            raise TTSAuthenticationError("ElevenLabs")

        if not text or not text.strip():
            return

        # If standard placeholder voice name passed, map to ElevenLabs voice ID
        voice_id = self.default_voice_id if voice in ("alloy", "default", "") else voice
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        self.logger.info(
            "Streaming audio from ElevenLabs TTS", voice_id=voice_id, model=self.model_id
        )

        try:
            async for chunk in self.http_client.stream(
                "POST",
                url,
                payload=payload,
                headers=self.headers,
            ):
                yield chunk

        except HTTPTimeoutError as e:
            self.logger.error("ElevenLabs TTS request timed out", url=url, exc=e)
            raise TTSConnectionError("ElevenLabs", url) from e

        except HTTPConnectionError as e:
            self.logger.error("ElevenLabs TTS connection error", url=url, exc=e)
            raise TTSConnectionError("ElevenLabs", url) from e

        except HTTPClientError as e:
            msg = str(e).lower()
            self.logger.error("ElevenLabs TTS client error", error=str(e), exc=e)
            if "401" in msg or "403" in msg or "auth" in msg or "api_key" in msg:
                raise TTSAuthenticationError("ElevenLabs") from e
            if "404" in msg or "voice" in msg:
                raise TTSVoiceNotFoundError("ElevenLabs", voice_id) from e
            if "429" in msg or "quota" in msg or "rate limit" in msg:
                raise TTSRateLimitError("ElevenLabs") from e
            raise TTSAudioGenerationError("ElevenLabs", str(e)) from e

        except TTSProviderError:
            raise

        except Exception as e:
            self.logger.error(
                "Unexpected error in ElevenLabs TTS stream", error=str(e), exc=e
            )
            raise TTSProviderError(f"Unexpected ElevenLabs TTS error: {str(e)}") from e
