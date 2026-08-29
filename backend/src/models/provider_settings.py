from __future__ import annotations
from datetime import datetime, timezone
import uuid
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from src.infra.postgres_adapter import Base
from src.core.enums import AIProvider


class ProviderSettings(Base):
    """
    SQLAlchemy Model representing the 'provider_settings' table.
    """

    __tablename__ = "provider_settings"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the provider settings",
    )
    provider_name: Mapped[AIProvider] = mapped_column(
        SQLEnum(AIProvider, name="ai_provider", native_enum=True),
        unique=True,
        nullable=False,
        comment="Name of the AI provider (e.g. OLLAMA, GEMINI, OPENAI)",
    )
    encrypted_api_key: Mapped[str] = mapped_column(
        String,
        nullable=True,
        comment="Encrypted API key for accessing the provider's API",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indicates whether this provider config is currently active",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when the provider settings were last updated",
    )

    def __repr__(self) -> str:
        return f"<ProviderSettings(provider_id={self.provider_id}, provider_name={self.provider_name}, is_active={self.is_active})>"
