import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.imedia_repository import IMediaRepository
from src.core.exceptions.database import (
    RepositoryError,
    MediaNotFoundError,
    DuplicateMediaError,
)
from src.models.media import Media


class MediaRepository(IMediaRepository):
    """
    SQLAlchemy implementation of the IMediaRepository for PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, media_id: uuid.UUID) -> Media | None:
        try:
            stmt = select(Media).where(Media.media_id == media_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving media by ID",
                media_id=media_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve media: {str(e)}") from e

    async def get_by_hash(self, file_hash: str) -> Media | None:
        try:
            stmt = select(Media).where(Media.file_hash == file_hash)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving media by hash",
                file_hash=file_hash,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve media by hash: {str(e)}") from e

    async def list_by_message(self, message_id: uuid.UUID) -> Sequence[Media]:
        try:
            stmt = (
                select(Media)
                .where(Media.message_id == message_id)
                .order_by(Media.uploaded_at.asc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing media for message",
                message_id=message_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list media: {str(e)}") from e

    async def create(self, media: Media) -> Media:
        try:
            self.session.add(media)
            await self.session.commit()
            await self.session.refresh(media)
            return media
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Media integrity violation on create",
                message_id=media.message_id,
                exc_info=e,
            )
            raise DuplicateMediaError("file_hash", media.file_hash) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating media",
                message_id=media.message_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create media: {str(e)}") from e

    async def update(self, media_id: uuid.UUID, **kwargs) -> Media:
        try:
            media = await self.get_by_id(media_id)
            if not media:
                raise MediaNotFoundError(media_id)

            for key, value in kwargs.items():
                if hasattr(media, key):
                    setattr(media, key, value)

            await self.session.commit()
            await self.session.refresh(media)
            return media
        except MediaNotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Media integrity violation on update",
                media_id=media_id,
                exc_info=e,
            )
            raise DuplicateMediaError("fields", str(kwargs)) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error updating media",
                media_id=media_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to update media: {str(e)}") from e

    async def delete(self, media_id: uuid.UUID) -> bool:
        try:
            media = await self.get_by_id(media_id)
            if not media:
                return False

            await self.session.delete(media)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting media",
                media_id=media_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete media: {str(e)}") from e
