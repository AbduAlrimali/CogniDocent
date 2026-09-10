"""Domain exceptions for LLM Provider interactions."""


class LLMProviderError(Exception):
    """Base exception for all LLM generation failures."""

    def __init__(self, message: str = "An error occurred during LLM generation."):
        self.message = message
        super().__init__(self.message)


class LLMConnectionError(LLMProviderError):
    """Raised when the provider is unreachable (e.g., local Ollama engine is down)."""

    def __init__(self, provider_name: str, endpoint: str):
        super().__init__(f"Failed to connect to {provider_name} at {endpoint}.")
        self.provider_name = provider_name
        self.endpoint = endpoint


class LLMAuthenticationError(LLMProviderError):
    """Raised when cloud API keys are invalid or missing."""

    def __init__(self, provider_name: str):
        super().__init__(
            f"Authentication failed for provider: {provider_name}. Check API keys."
        )


class LLMContextLimitExceededError(LLMProviderError):
    """Raised when the conversation history and retrieved documents exceed the model's token limit."""

    def __init__(self, max_tokens: int, requested_tokens: int):
        super().__init__(
            f"Context limit exceeded. Model allows {max_tokens}, but prompt requires {requested_tokens}."
        )


class LLMRateLimitError(LLMProviderError):
    """Raised when a cloud provider throttles the application."""

    def __init__(self, retry_after_seconds: int):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after_seconds} seconds."
        )
        self.retry_after_seconds = retry_after_seconds
