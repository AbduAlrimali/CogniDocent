import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.imessage_repository import IMessageRepository
from src.core.exceptions.database import (
    RepositoryError,
    MessageNotFoundError,
    DuplicateMessageError,
)
from src.models.message import Message


class MessageRepository(IMessageRepository):
    """
    SQLAlchemy implementation of the IMessageRepository for PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, message_id: uuid.UUID) -> Message | None:
        try:
            stmt = select(Message).where(Message.message_id == message_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving message by ID",
                message_id=message_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve message: {str(e)}") from e

    async def list_by_chat(self, chat_id: uuid.UUID) -> Sequence[Message]:
        try:
            stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing messages for chat",
                chat_id=chat_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list messages: {str(e)}") from e

    async def create(self, message: Message) -> Message:
        try:
            self.session.add(message)
            await self.session.commit()
            await self.session.refresh(message)
            return message
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Message integrity violation on create",
                chat_id=message.chat_id,
                exc_info=e,
            )
            raise DuplicateMessageError("message_id", message.message_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating message",
                chat_id=message.chat_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create message: {str(e)}") from e

    async def delete(self, message_id: uuid.UUID) -> bool:
        try:
            message = await self.get_by_id(message_id)
            if not message:
                return False

            await self.session.delete(message)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting message",
                message_id=message_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete message: {str(e)}") from e

    async def get_recent_history(self, chat_id: uuid.UUID, limit: int = 50) -> Sequence[Message]:
        try:
            # Query recent messages descending to get the last N, then reverse to output chronologically
            stmt = (
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            messages = list(result.scalars().all())
            messages.reverse()
            return messages
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error fetching recent message history",
                chat_id=chat_id,
                limit=limit,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to fetch recent history: {str(e)}") from e
