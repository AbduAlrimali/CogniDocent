from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class DocumentPageBase(BaseModel):
    doc_id: uuid.UUID
    page_num: int
    content: str
    content_vector: Optional[List[float]] = None
    deep_content: Optional[str] = None
    deep_content_vector: Optional[List[float]] = None


class DocumentPageCreate(DocumentPageBase):
    pass


class DocumentPageUpdate(BaseModel):
    content: Optional[str] = None
    content_vector: Optional[List[float]] = None
    deep_content: Optional[str] = None
    deep_content_vector: Optional[List[float]] = None


class PageUpdateDTO(BaseModel):
    page_id: uuid.UUID
    deep_content: Optional[str] = None
    deep_content_vector: Optional[List[float]] = None
    content: Optional[str] = None
    content_vector: Optional[List[float]] = None


class DocumentPageResponse(DocumentPageBase):
    model_config = ConfigDict(from_attributes=True)

    page_id: uuid.UUID


class EmbeddingIndexMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: uuid.UUID
    active_model: str
    dimensions: int
    updated_at: datetime
