from dataclasses import dataclass
from typing import Optional
import uuid
from src.core.dtos.llm_provider_dtos import SystemAIConfigDTO


@dataclass
class ThreadStateDTO:
    """Internal graph state, hidden from the domain."""

    project_id: uuid.UUID
    document_id: uuid.UUID
    config: Optional[SystemAIConfigDTO] = None
