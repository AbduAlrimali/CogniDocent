from dataclasses import dataclass
from typing import Any


@dataclass
class HTTPResponse:
    """A Python representation of an HTTP Response."""

    status_code: int
    body: dict[str, Any] | list[Any] | None
    headers: dict[str, str]
    text: str

    @property
    def is_success(self) -> bool:
        """Helper to easily check if the request was successful."""
        return 200 <= self.status_code < 300
