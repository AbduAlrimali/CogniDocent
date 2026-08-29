from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.core.enums import Role
import uuid
from src.schemas.media import MediaResponse


class CitationItem(BaseModel):
    page_num: int
    snippet: str
    score: Optional[float] = None


class MessageBase(BaseModel):
    role: Role
    content: str
    citations: Optional[List[CitationItem]] = None


class MessageCreate(MessageBase):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    thinking_mode: Optional[str] = None
    token_count: Optional[int] = None
    latency_ms: Optional[int] = None


class MessageQueryParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_order: str = "asc"  # Messages are typically fetched chronologically


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    message_id: uuid.UUID
    chat_id: uuid.UUID
    media: Optional[List[MediaResponse]] = None
    created_at: datetime
    token_count: Optional[int] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    thinking_mode: Optional[str] = None
