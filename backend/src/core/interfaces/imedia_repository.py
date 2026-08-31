from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.models.media import Media


class IMediaRepository(ABC):
    """
    Interface for Media repository operations (Port).
    """

    @abstractmethod
    async def get_by_id(self, media_id: uuid.UUID) -> Media | None:
        """
        Retrieve a media file by its ID.
        """
        pass

    @abstractmethod
    async def get_by_hash(self, file_hash: str) -> Media | None:
        """
        Retrieve a media record by its unique content hash (useful for duplicate detection).
        """
        pass

    @abstractmethod
    async def list_by_message(self, message_id: uuid.UUID) -> Sequence[Media]:
        """
        Retrieve all media attachments associated with a message.
        """
        pass

    @abstractmethod
    async def create(self, media: Media) -> Media:
        """
        Save a new media attachment record.
        """
        pass

    @abstractmethod
    async def update(self, media_id: uuid.UUID, **kwargs) -> Media:
        """
        Update an existing media record.
        """
        pass

    @abstractmethod
    async def delete(self, media_id: uuid.UUID) -> bool:
        """
        Delete a media attachment record.
        """
        pass
