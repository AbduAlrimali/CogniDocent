from abc import ABC, abstractmethod
from src.core.dtos.llm_provider_dtos import LLMRouteConfigDTO


class IVisionProvider(ABC):
    @abstractmethod
    async def extract_markdown(self, image_bytes: bytes, config: LLMRouteConfigDTO) -> str:
        pass
