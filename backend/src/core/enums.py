from enum import Enum


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AIProvider(str, Enum):
    """
    Enum representing supported AI/LLM providers in the application.
    Easy to extend in the future with new providers.
    """

    OLLAMA = "OLLAMA"
    GEMINI = "GEMINI"
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"


class UploadStatus(str, Enum):
    """
    Enum representing the status of a file upload.
    """

    PROCESSING = "processing"
    COMPLETED = "completed"
    INFECTED = "infected"
    FAILED = "failed"
