from __future__ import annotations
from datetime import datetime, timezone
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infra.postgres_adapter import Base
from src.core.enums import AIProvider

if TYPE_CHECKING:
    from src.models.project import Project
    from src.models.message import Message


class Chat(Base):
    """
    SQLAlchemy Model representing the 'chats' table.
    """

    __tablename__ = "chats"

    chat_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the chat",
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the associated project",
    )
    title: Mapped[str] = mapped_column(
        String, nullable=False, comment="Title/Name of the chat session"
    )
    ai_provider: Mapped[AIProvider] = mapped_column(
        SQLEnum(AIProvider, name="ai_provider", native_enum=True),
        nullable=False,
        default=AIProvider.OLLAMA,
        server_default=AIProvider.OLLAMA.value,
        comment="AI Provider used for this chat",
    )
    ai_model: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="AI Model version used for this chat (e.g. gpt-4o, claude-3-5-sonnet)",
    )
    thinking_mode: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Optional setting indicating the reasoning or thinking mode",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the chat was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the chat was last updated",
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates whether the chat is archived",
    )
    chat_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Additional chat session metadata stored as JSON",
    )

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="chats")
    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Chat(chat_id={self.chat_id}, title={self.title}, ai_provider={self.ai_provider}, ai_model={self.ai_model})>"
