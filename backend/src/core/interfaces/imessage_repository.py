from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.models.message import Message


class IMessageRepository(ABC):
    """
    Interface for Message repository operations (Port).
    """

    @abstractmethod
    async def get_by_id(self, message_id: uuid.UUID) -> Message | None:
        """
        Retrieve a message by its ID.
        """
        pass

    @abstractmethod
    async def list_by_chat(self, chat_id: uuid.UUID) -> Sequence[Message]:
        """
        Retrieve all messages for a specific chat, ordered by creation time.
        """
        pass

    @abstractmethod
    async def create(self, message: Message) -> Message:
        """
        Save a new message.
        """
        pass

    @abstractmethod
    async def delete(self, message_id: uuid.UUID) -> bool:
        """
        Delete a message by its ID.
        """
        pass

    @abstractmethod
    async def get_recent_history(self, chat_id: uuid.UUID, limit: int = 50) -> Sequence[Message]:
        """
        Retrieve recent message history for a chat session, ordered chronologically.
        """
        pass
