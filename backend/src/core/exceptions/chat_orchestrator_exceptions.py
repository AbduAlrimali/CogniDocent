"""Domain exceptions raised during conversation orchestration and multi-step reasoning."""


class OrchestrationError(Exception):
    """Base exception for all orchestration failures."""

    def __init__(self, message: str = "An error occurred during chat orchestration."):
        self.message = message
        super().__init__(self.message)


class OrchestrationTimeoutError(OrchestrationError):
    """Raised when graph execution or a tool execution exceeds the permitted time limit."""

    def __init__(self, timeout_seconds: float):
        super().__init__(
            f"Orchestration exceeded maximum timeout of {timeout_seconds} seconds."
        )
        self.timeout_seconds = timeout_seconds


class MaxIterationsReachedError(OrchestrationError):
    """Raised when the agent exceeds the allowed cyclic recursion depth."""

    def __init__(self, max_iterations: int):
        super().__init__(
            f"Agent stopped: recursion limit of {max_iterations} iterations reached."
        )
        self.max_iterations = max_iterations


class ToolExecutionError(OrchestrationError):
    """Raised when an internal tool or sub-agent fails catastrophically."""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(f"Tool '{tool_name}' failed during execution: {reason}")
        self.tool_name = tool_name
        self.reason = reason


class ChatSessionStateError(OrchestrationError):
    """Raised when the conversation checkpoint/state cannot be loaded or updated."""

    def __init__(self, chat_id: str, reason: str):
        super().__init__(
            f"Failed to process state for chat session '{chat_id}': {reason}"
        )
        self.chat_id = chat_id
        self.reason = reason
