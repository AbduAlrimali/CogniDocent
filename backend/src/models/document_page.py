from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from src.infra.postgres_adapter import Base

if TYPE_CHECKING:
    from src.models.document import Document


class DocumentPage(Base):
    """
    SQLAlchemy Model representing the 'document_pages' table.
    Stores extracted page-level content with vector search indexing.
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
    content_vector: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
        comment="Vector embedding of parsed text"
    )
    deep_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Deep parsed text extracted via Vision LLM"
    )
    deep_content_vector: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
        comment="Vector embedding of deep parsed text"
    )

    # Relationships
    document: Mapped[Document] = relationship(
        "Document",
        back_populates="pages"
    )

    # HNSW indexes for vector cosine similarity
    __table_args__ = (
        Index(
            "idx_document_pages_content_vector",
            "content_vector",
            postgresql_using="hnsw",
            postgresql_ops={"content_vector": "vector_cosine_ops"}
        ),
        Index(
            "idx_document_pages_deep_content_vector",
            "deep_content_vector",
            postgresql_using="hnsw",
            postgresql_ops={"deep_content_vector": "vector_cosine_ops"}
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentPage(page_id={self.page_id}, doc_id={self.doc_id}, page_num={self.page_num})>"
