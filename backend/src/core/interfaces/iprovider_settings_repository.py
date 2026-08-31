from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.core.enums import AIProvider
from src.models.provider_settings import ProviderSettings


class IProviderSettingsRepository(ABC):
    """
    Interface for ProviderSettings repository operations (Port).
    """

    @abstractmethod
    async def get_by_id(self, provider_id: uuid.UUID) -> ProviderSettings | None:
        """
        Retrieve provider settings by their unique ID.
        """
        pass

    @abstractmethod
    async def get_by_provider(self, provider_name: AIProvider) -> ProviderSettings | None:
        """
        Retrieve settings for a specific AI provider.
        """
        pass

    @abstractmethod
    async def get_active_provider(self) -> ProviderSettings | None:
        """
        Retrieve the currently active AI provider settings.
        """
        pass

    @abstractmethod
    async def list_all(self) -> Sequence[ProviderSettings]:
        """
        Retrieve settings for all AI providers.
        """
        pass

    @abstractmethod
    async def create(self, settings: ProviderSettings) -> ProviderSettings:
        """
        Save new settings for an AI provider.
        """
        pass

    @abstractmethod
    async def update(self, provider_name: AIProvider, **kwargs) -> ProviderSettings:
        """
        Update settings for a specific AI provider.
        """
        pass

    @abstractmethod
    async def delete(self, provider_name: AIProvider) -> bool:
        """
        Delete settings for an AI provider.
        """
        pass
