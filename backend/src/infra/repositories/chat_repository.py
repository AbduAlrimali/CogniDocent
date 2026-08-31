import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.ichat_repository import IChatRepository
from src.core.exceptions.database import (
    RepositoryError,
    ChatNotFoundError,
    DuplicateChatError,
)
from src.models.chat import Chat


class ChatRepository(IChatRepository):
    """
    SQLAlchemy implementation of the IChatRepository for PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, chat_id: uuid.UUID) -> Chat | None:
        try:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving chat by ID",
                chat_id=chat_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve chat: {str(e)}") from e

    async def list_by_project(
        self, project_id: uuid.UUID, include_archived: bool = False
    ) -> Sequence[Chat]:
        try:
            stmt = select(Chat).where(Chat.project_id == project_id)
            if not include_archived:
                stmt = stmt.where(Chat.is_archived == False)
            stmt = stmt.order_by(Chat.created_at.desc())
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing chats for project",
                project_id=project_id,
                include_archived=include_archived,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list chats: {str(e)}") from e

    async def create(self, chat: Chat) -> Chat:
        try:
            self.session.add(chat)
            await self.session.commit()
            await self.session.refresh(chat)
            return chat
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Chat integrity violation on create",
                project_id=chat.project_id,
                exc_info=e,
            )
            raise DuplicateChatError("chat_id", chat.chat_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating chat",
                project_id=chat.project_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create chat: {str(e)}") from e

    async def update(self, chat_id: uuid.UUID, **kwargs) -> Chat:
        try:
            chat = await self.get_by_id(chat_id)
            if not chat:
                raise ChatNotFoundError(chat_id)

            for key, value in kwargs.items():
                if hasattr(chat, key):
                    setattr(chat, key, value)

            await self.session.commit()
            await self.session.refresh(chat)
            return chat
        except ChatNotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Chat integrity violation on update",
                chat_id=chat_id,
                exc_info=e,
            )
            raise DuplicateChatError("fields", str(kwargs)) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error updating chat",
                chat_id=chat_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to update chat: {str(e)}") from e

    async def delete(self, chat_id: uuid.UUID) -> bool:
        try:
            chat = await self.get_by_id(chat_id)
            if not chat:
                return False

            await self.session.delete(chat)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting chat",
                chat_id=chat_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete chat: {str(e)}") from e
