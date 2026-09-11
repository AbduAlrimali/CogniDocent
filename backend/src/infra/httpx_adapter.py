from typing import Any, AsyncGenerator
import json
import httpx

from src.core.interfaces.ihttp_client import IHTTPClient
from src.core.interfaces.ilogger import ILogger
from src.core.dtos.http_dtos import HTTPResponse
from src.core.exceptions.http_exceptions import (
    HTTPClientError,
    HTTPConnectionError,
    HTTPTimeoutError,
    HTTPDecodeError,
)


class HttpxClient(IHTTPClient):
    def __init__(self, client: httpx.AsyncClient, logger: ILogger):
        self._client = client
        self._logger = logger

    async def _execute(self, method: str, url: str, **kwargs) -> HTTPResponse:
        """Centralized method to execute requests and translate exceptions."""
        self._logger.info("Executing HTTP request", method=method, url=url)
        try:
            response = await self._client.request(method, url, **kwargs)

            if response.is_error:
                self._logger.warning(
                    "HTTP request returned an error status",
                    method=method,
                    url=url,
                    status_code=response.status_code,
                )

            return self._map_response(response)

        except httpx.TimeoutException as e:
            self._logger.error("HTTP request timed out", method=method, url=url, exc=e)
            raise HTTPTimeoutError("HTTP request timed out.") from e

        except httpx.RequestError as e:
            self._logger.error("HTTP connection error", method=method, url=url, exc=e)
            raise HTTPConnectionError("HTTP connection failed.") from e

        except HTTPClientError:
            raise
        except Exception as e:
            self._logger.error(
                "Unexpected HTTP client error", method=method, url=url, exc=e
            )
            raise HTTPClientError("An unexpected HTTP error occurred.") from e

    def _map_response(self, response: httpx.Response) -> HTTPResponse:
        """Parses the body into JSON, raising our custom decode error if it fails."""
        if not response.content:
            parsed_body = None
        else:
            try:
                parsed_body = response.json()
            except json.JSONDecodeError as e:
                self._logger.error(
                    "Failed to decode HTTP response JSON",
                    status_code=response.status_code,
                    exc=e,
                )
                raise HTTPDecodeError("Failed to parse JSON response.") from e

        return HTTPResponse(
            status_code=response.status_code,
            body=parsed_body,
            text=response.text,
            headers=dict(response.headers),
        )

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = True,
    ) -> HTTPResponse:
        return await self._execute(
            "GET",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

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
        return await self._execute(
            "POST",
            url,
            json=payload,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

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
        return await self._execute(
            "PUT",
            url,
            json=payload,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

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
        return await self._execute(
            "PATCH",
            url,
            json=payload,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
        follow_redirects: bool = False,
    ) -> HTTPResponse:
        return await self._execute(
            "DELETE",
            url,
            params=params,
            headers=headers,
            timeout=timeout,
            follow_redirects=follow_redirects,
        )

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
        self._logger.info("Executing HTTP streaming request", method=method, url=url)
        try:
            async with self._client.stream(
                method,
                url,
                json=payload,
                data=data,
                files=files,
                params=params,
                headers=headers,
                timeout=timeout,
                follow_redirects=follow_redirects,
            ) as response:
                if response.is_error:
                    error_bytes = await response.aread()
                    error_msg = error_bytes.decode("utf-8", errors="replace")
                    self._logger.warning(
                        "HTTP streaming request returned an error status",
                        method=method,
                        url=url,
                        status_code=response.status_code,
                        error=error_msg,
                    )
                    raise HTTPClientError(
                        f"HTTP streaming error ({response.status_code}): {error_msg}"
                    )

                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                    yield chunk

        except httpx.TimeoutException as e:
            self._logger.error("HTTP stream timed out", method=method, url=url, exc=e)
            raise HTTPTimeoutError("HTTP request timed out.") from e
        except httpx.RequestError as e:
            self._logger.error("HTTP stream connection error", method=method, url=url, exc=e)
            raise HTTPConnectionError("HTTP connection failed.") from e
        except HTTPClientError:
            raise
        except Exception as e:
            self._logger.error(
                "Unexpected HTTP stream error", method=method, url=url, exc=e
            )
            raise HTTPClientError(f"Unexpected streaming error: {str(e)}") from e

    async def close(self):
        await self._client.aclose()
