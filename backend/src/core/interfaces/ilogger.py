from abc import ABC, abstractmethod
from typing import Any


class ILogger(ABC):
    """
    Interface for a structured logger following Clean Architecture principles.

    This interface decouples the core domain from specific logging libraries
    (e.g., Loguru, structlog, or standard logging). It supports structured
    context via keyword arguments to allow for advanced filtering and observability.
    """

    @abstractmethod
    def debug(self, msg: str, **kwargs: Any) -> None:
        """
        Log a message with DEBUG level. Used for diagnostic information
        useful for developers during development.
        Raises: LoggerDispatchError if the logging backend is unreachable.
        """
        ...

    @abstractmethod
    def info(self, msg: str, **kwargs: Any) -> None:
        """
        Log a message with INFO level. Used for general operational
        messages (e.g., 'User logged in', 'Process started').
        """
        ...

    @abstractmethod
    def warning(self, msg: str, **kwargs: Any) -> None:
        """
        Log a message with WARNING level. Used for unexpected events that
        don't stop the app but might require attention.
        """
        ...

    @abstractmethod
    def error(self, msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """
        Log a message with ERROR level. Used for events that caused a
        failure in a specific operation.

        Args:
            msg: The error description.
            exc: The exception instance for traceback capture.
            **kwargs: Metadata (e.g., user_id, request_id).
        """
        ...

    @abstractmethod
    def critical(self, msg: str, exc_info: Any = None, **kwargs: Any) -> None:
        """
        Log a message with CRITICAL level. Used for severe failures that
        might require immediate manual intervention.
        """
        ...
