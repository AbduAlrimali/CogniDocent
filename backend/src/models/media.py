from __future__ import annotations
from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infra.postgres_adapter import Base

if TYPE_CHECKING:
    from src.models.message import Message


class Media(Base):
    """
    SQLAlchemy Model representing the 'media' table.
    """
    __tablename__ = "media"

    media_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the media file"
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the associated message"
    )
    filename: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Original filename of the media attachment"
    )
    file_path: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Physical path where the file is stored"
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Size of the file in bytes"
    )
    file_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Hash of the file content for duplicate checking"
    )
    content_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="MIME/Content type of the media file"
    )
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Processing/Upload status of the media"
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the media file was uploaded"
    )

    # Relationships
    message: Mapped[Message] = relationship(
        "Message",
        back_populates="media"
    )

    def __repr__(self) -> str:
        return f"<Media(media_id={self.media_id}, filename={self.filename}, status={self.status})>"
