from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.models.chat import Chat


class IChatRepository(ABC):
    """
    Interface for Chat repository operations (Port).
    """

    @abstractmethod
    async def get_by_id(self, chat_id: uuid.UUID) -> Chat | None:
        """
        Retrieve a chat session by its ID.
        """
        pass

    @abstractmethod
    async def list_by_project(self, project_id: uuid.UUID, include_archived: bool = False) -> Sequence[Chat]:
        """
        Retrieve all chat sessions for a specific project.
        """
        pass

    @abstractmethod
    async def create(self, chat: Chat) -> Chat:
        """
        Create a new chat session.
        """
        pass

    @abstractmethod
    async def update(self, chat_id: uuid.UUID, **kwargs) -> Chat:
        """
        Update an existing chat session.
        """
        pass

    @abstractmethod
    async def delete(self, chat_id: uuid.UUID) -> bool:
        """
        Delete a chat session by its ID.
        """
        pass
