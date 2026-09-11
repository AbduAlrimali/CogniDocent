# src/core/ports/itts_provider.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class ITextToSpeechProvider(ABC):
    @abstractmethod
    async def stream_audio(
        self, text: str, voice: str = "alloy"
    ) -> AsyncGenerator[bytes, None]:
        """
        Takes plain text and streams back audio bytes (e.g., MP3/Opus).

        Raises:
            TTSConnectionError: If the TTS service cannot be reached or times out.
            TTSAuthenticationError: If API credentials fail or are missing.
            TTSRateLimitError: If rate limits or quotas are exceeded.
            TTSVoiceNotFoundError: If the requested voice does not exist.
            TTSAudioGenerationError: If audio synthesis fails on the provider side.
            TTSProviderError: For any other TTS generation errors.
        """
        pass
