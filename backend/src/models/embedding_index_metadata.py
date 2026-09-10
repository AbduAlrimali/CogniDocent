from __future__ import annotations
from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infra.postgres_adapter import Base

if TYPE_CHECKING:
    from src.models.project import Project


class EmbeddingIndexMetadata(Base):
    """
    SQLAlchemy Model representing the 'embedding_index_metadata' table.
    Stores project-specific embedding model metadata.
    """
    __tablename__ = "embedding_index_metadata"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        primary_key=True,
        comment="Associated project ID"
    )
    active_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="nomic-embed-text-v2-moe",
        comment="Active embedding model name"
    )
    dimensions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=768,
        comment="Vector dimension count for the active model"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of the most recent model configuration update"
    )

    # Relationships
    project: Mapped[Project] = relationship(
        "Project",
        back_populates="embedding_metadata"
    )

    def __repr__(self) -> str:
        return (
            f"<EmbeddingIndexMetadata(project_id={self.project_id}, "
            f"active_model='{self.active_model}', dimensions={self.dimensions})>"
        )
