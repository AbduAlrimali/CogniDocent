from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, Integer, ForeignKey, Text, Index, JSON
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infra.postgres_adapter import Base

if TYPE_CHECKING:
    from src.models.document import Document


class DocumentPage(Base):
    """
    SQLAlchemy Model representing the 'document_pages' table.
    Stores extracted page-level content with search indexing.
    """
    __tablename__ = "document_pages"

    page_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the document page"
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent document"
    )
    page_num: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="The page number of this page in the document"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Text content extracted from the document page"
    )
    markdown_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Markdown content extracted from VLM deep parsing"
    )
    page_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Page-level metadata stored as JSON"
    )
    search_vector: Mapped[Any | None] = mapped_column(
        TSVECTOR,
        nullable=True,
        comment="Postgres tsvector for full-text search indexing"
    )

    # Relationships
    document: Mapped[Document] = relationship(
        "Document",
        back_populates="pages"
    )

    # GIN Index for fast full-text searches on the search_vector
    __table_args__ = (
        Index(
            "idx_document_pages_search_vector",
            "search_vector",
            postgresql_using="gin"
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentPage(page_id={self.page_id}, doc_id={self.doc_id}, page_num={self.page_num})>"
