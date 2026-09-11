class OrchestratorError(Exception):
    """Base exception for all chat orchestration failures."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class GraphRecursionLimitError(OrchestratorError):
    """Raised when the agent enters an infinite loop or exceeds max steps."""

    pass


class ContextWindowExceededError(OrchestratorError):
    """Raised when the conversation history + context exceeds the LLM token budget."""

    pass


class ToolExecutionError(OrchestratorError):
    """Raised when an orchestration tool fails irrecoverably during execution."""

    def __init__(self, tool_name: str, message: str, details: dict | None = None):
        super().__init__(f"Tool '{tool_name}' failed: {message}", details)
        self.tool_name = tool_name


class ProviderUnavailableError(OrchestratorError):
    """Raised when the underlying LLM provider times out or is unreachable."""

    pass


class CorruptedThreadStateError(OrchestratorError):
    """Raised when the checkpointer fails to deserialize or load thread history."""

    pass
