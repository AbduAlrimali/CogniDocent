"""Domain exceptions for Text-To-Speech (TTS) Provider interactions."""

from typing import Optional


class TTSProviderError(Exception):
    """Base exception for all TTS generation failures."""

    def __init__(self, message: str = "An error occurred during TTS audio generation.", details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TTSConnectionError(TTSProviderError):
    """Raised when the TTS provider endpoint is unreachable or network connection fails."""

    def __init__(self, provider_name: str, endpoint: str):
        super().__init__(f"Failed to connect to TTS provider {provider_name} at {endpoint}.")
        self.provider_name = provider_name
        self.endpoint = endpoint


class TTSAuthenticationError(TTSProviderError):
    """Raised when TTS API keys are invalid, expired, or missing."""

    def __init__(self, provider_name: str):
        super().__init__(f"Authentication failed for TTS provider: {provider_name}. Check API credentials.")
        self.provider_name = provider_name


class TTSRateLimitError(TTSProviderError):
    """Raised when a TTS provider throttles requests."""

    def __init__(self, provider_name: str, retry_after_seconds: int = 60):
        super().__init__(f"Rate limit exceeded for TTS provider {provider_name}. Retry after {retry_after_seconds} seconds.")
        self.provider_name = provider_name
        self.retry_after_seconds = retry_after_seconds


class TTSAudioGenerationError(TTSProviderError):
    """Raised when audio synthesis fails on the provider side."""

    def __init__(self, provider_name: str, reason: str):
        super().__init__(f"TTS provider {provider_name} failed to synthesize audio: {reason}")
        self.provider_name = provider_name
        self.reason = reason


class TTSVoiceNotFoundError(TTSProviderError):
    """Raised when the requested voice ID or name does not exist on the provider."""

    def __init__(self, provider_name: str, voice: str):
        super().__init__(f"Voice '{voice}' not found for TTS provider {provider_name}.")
        self.provider_name = provider_name
        self.voice = voice
