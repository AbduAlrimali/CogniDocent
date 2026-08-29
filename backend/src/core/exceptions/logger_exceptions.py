class LoggerError(Exception):
    """Base exception for all logging-related errors."""

    def __init__(self, message: str = "An internal logging error occurred"):
        self.message = message
        super().__init__(self.message)


class LoggerInitializationError(LoggerError):
    """Raised when the logger fails to start (e.g., invalid config)."""

    pass


class LoggerConfigurationError(LoggerError):
    """Raised when provided logging metadata or levels are invalid."""

    pass


class LoggerDispatchError(LoggerError):
    """Raised when the logger cannot send logs to its destination (e.g., Disk Full)."""

    pass
