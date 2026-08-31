"""Domain and application exceptions for the fast PDF parsing subsystem."""


class FastParserError(Exception):
    """Base exception for all fast parser failures."""

    def __init__(
        self, message: str = "An error occurred during fast document parsing."
    ):
        self.message = message
        super().__init__(self.message)


class DocumentNotFoundError(FastParserError):
    """Raised when the specified file path does not exist."""

    def __init__(self, file_path: str):
        super().__init__(f"Document not found at path: '{file_path}'")
        self.file_path = file_path


class DocumentCorruptedError(FastParserError):
    """Raised when a PDF file header or xref table is malformed/unreadable."""

    def __init__(self, file_path: str, reason: str = "Invalid file structure"):
        super().__init__(
            f"Document at '{file_path}' is corrupted or unreadable: {reason}"
        )
        self.file_path = file_path
        self.reason = reason


class DocumentEncryptedError(FastParserError):
    """Raised when a PDF requires an authentication password for extraction."""

    def __init__(self, file_path: str):
        super().__init__(
            f"Document at '{file_path}' is password-protected or encrypted."
        )
        self.file_path = file_path


class PageExtractionError(FastParserError):
    """Raised when an individual page fails extraction during bulk or stream operations."""

    def __init__(self, file_path: str, page_num: int, reason: str):
        super().__init__(
            f"Failed to extract text from page {page_num} in '{file_path}':"
            f" {reason}"
        )
        self.file_path = file_path
        self.page_num = page_num
        self.reason = reason


class ParserResourceLimitError(FastParserError):
    """Raised when a document exceeds memory, decompression, or execution timeout thresholds."""

    def __init__(self, file_path: str, limit_type: str):
        super().__init__(
            f"Resource safety limit exceeded ({limit_type}) while parsing:"
            f" '{file_path}'"
        )
        self.file_path = file_path
        self.limit_type = limit_type
