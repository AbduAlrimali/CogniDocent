from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DocumentPageBase(BaseModel):
    doc_id: uuid.UUID
    page_num: int
    content: str
    markdown_content: Optional[str] = None
    page_metadata: Optional[Dict[str, Any]] = None


class DocumentPageCreate(DocumentPageBase):
    pass


class DocumentPageUpdate(BaseModel):
    content: Optional[str] = None
    markdown_content: Optional[str] = None
    page_metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class DocumentPageResponse(DocumentPageBase):
    model_config = ConfigDict(from_attributes=True)

    page_id: uuid.UUID
    embedding: Optional[List[float]] = None


class EmbeddingIndexMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: uuid.UUID
    active_model: str
    dimensions: int
    updated_at: datetime
