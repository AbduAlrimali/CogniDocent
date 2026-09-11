"""Domain exceptions for document processing, ingestion, and lifecycle."""

import uuid


class DocumentError(Exception):
    """Base exception for document domain errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DocumentNotParsedError(DocumentError):
    """Raised when an operation requires a document to be parsed, but it has not been parsed yet."""

    def __init__(
        self,
        doc_id: uuid.UUID,
        reason: str = "Document has not been parsed or ingested yet.",
    ):
        self.doc_id = doc_id
        self.reason = reason
        super().__init__(f"Document '{doc_id}' is not parsed: {reason}")
