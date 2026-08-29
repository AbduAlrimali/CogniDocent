from __future__ import annotations
from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infra.postgres_adapter import Base

if TYPE_CHECKING:
    from src.models.document import Document
    from src.models.chat import Chat


class Project(Base):
    """
    SQLAlchemy Model representing the 'projects' table.
    """
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the project"
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Reference to the associated document (one-to-one)"
    )
    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Title of the project"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the project was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the project was last updated"
    )
    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Optional description of the project"
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates whether the project is archived"
    )
    settings: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Project settings stored as JSON"
    )

    # Relationships
    document: Mapped[Document] = relationship(
        "Document",
        back_populates="project"
    )
    chats: Mapped[list[Chat]] = relationship(
        "Chat",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(project_id={self.project_id}, title={self.title}, is_archived={self.is_archived})>"
