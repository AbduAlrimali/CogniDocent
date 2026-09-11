from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator
from src.core.dtos.http_dtos import HTTPResponse


class IHTTPClient(ABC):
    """The HTTP Client Interface."""

    @abstractmethod
    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = True,
    ) -> HTTPResponse:
        """Send a GET request."""
        ...

    @abstractmethod
    async def post(
        self,
        url: str,
        *,
        payload: dict[str, Any] | None = None,  # JSON (application/json)
        data: dict[str, Any] | None = None,  # Form (x-www-form-urlencoded)
        files: dict[str, Any] | None = None,  # Multipart (multipart/form-data)
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,  # Support for URL params in POST
        timeout: float | None = None,
        follow_redirects: bool = True,
    ) -> HTTPResponse:
        """Send a POST request."""
        ...

    @abstractmethod
    async def put(
        self,
        url: str,
        *,
        payload: dict[str, Any] | None = None,  # JSON (application/json)
        data: dict[str, Any] | None = None,  # Form (x-www-form-urlencoded)
        files: dict[str, Any] | None = None,  # Multipart (multipart/form-data)
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,  # Support for URL params in POST
        timeout: float | None = None,
        follow_redirects: bool = True,
    ) -> HTTPResponse:
        """Send a PUT request."""
        ...

    @abstractmethod
    async def patch(
        self,
        url: str,
        *,
        payload: dict[str, Any] | None = None,  # JSON (application/json)
        data: dict[str, Any] | None = None,  # Form (x-www-form-urlencoded)
        files: dict[str, Any] | None = None,  # Multipart (multipart/form-data)
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,  # Support for URL params in POST
        timeout: float | None = None,
        follow_redirects: bool = True,
    ) -> HTTPResponse:
        """Send a PATCH request."""
        ...

    @abstractmethod
    async def delete(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> HTTPResponse:
        """Send a DELETE request."""
        ...

    @abstractmethod
    async def stream(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = True,
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        """Stream response bytes from an HTTP request."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close connections."""
        ...
