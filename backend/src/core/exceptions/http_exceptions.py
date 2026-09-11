from typing import Any


class HTTPClientError(Exception):
    """Base exception for all HTTP Client errors."""

    pass


class HTTPConnectionError(HTTPClientError):
    """Raised when a connection to the server fails."""

    pass


class HTTPTimeoutError(HTTPClientError):
    """Raised when a request times out."""

    pass


class HTTPDecodeError(HTTPClientError):
    """Raised when the response body cannot be decoded into the expected format."""

    pass


class HTTPStatusError(HTTPClientError):
    """Raised when the HTTP response has a 4xx or 5xx status code."""

    def __init__(self, message: str, status_code: int, response_body: Any):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
