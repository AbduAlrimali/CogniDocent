import uuid
from typing import Sequence
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.enums import AIProvider
from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.iprovider_settings_repository import IProviderSettingsRepository
from src.core.exceptions.database import (
    RepositoryError,
    ProviderSettingsNotFoundError,
    DuplicateProviderSettingsError,
)
from src.models.provider_settings import ProviderSettings


class ProviderSettingsRepository(IProviderSettingsRepository):
    """
    SQLAlchemy implementation of the IProviderSettingsRepository for PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, provider_id: uuid.UUID) -> ProviderSettings | None:
        try:
            stmt = select(ProviderSettings).where(ProviderSettings.provider_id == provider_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving provider settings by ID",
                provider_id=provider_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve provider settings: {str(e)}") from e

    async def get_by_provider(self, provider_name: AIProvider) -> ProviderSettings | None:
        try:
            stmt = select(ProviderSettings).where(ProviderSettings.provider_name == provider_name)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving provider settings by name",
                provider_name=provider_name,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve provider settings: {str(e)}") from e

    async def get_active_provider(self) -> ProviderSettings | None:
        try:
            stmt = select(ProviderSettings).where(ProviderSettings.is_active == True)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving active provider settings",
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve active provider settings: {str(e)}") from e

    async def list_all(self) -> Sequence[ProviderSettings]:
        try:
            stmt = select(ProviderSettings).order_by(ProviderSettings.provider_name.asc())
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing provider settings",
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list provider settings: {str(e)}") from e

    async def create(self, settings: ProviderSettings) -> ProviderSettings:
        try:
            if settings.is_active:
                # Set all other providers to inactive
                await self.session.execute(
                    sql_update(ProviderSettings)
                    .where(ProviderSettings.provider_id != settings.provider_id)
                    .values(is_active=False)
                )

            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
            return settings
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Provider settings integrity violation on create",
                provider_name=settings.provider_name,
                exc_info=e,
            )
            raise DuplicateProviderSettingsError("provider_name", settings.provider_name) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating provider settings",
                provider_name=settings.provider_name,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create provider settings: {str(e)}") from e

    async def update(self, provider_name: AIProvider, **kwargs) -> ProviderSettings:
        try:
            settings = await self.get_by_provider(provider_name)
            if not settings:
                raise ProviderSettingsNotFoundError(provider_name)

            if kwargs.get("is_active"):
                # Set all other providers to inactive
                await self.session.execute(
                    sql_update(ProviderSettings)
                    .where(ProviderSettings.provider_name != provider_name)
                    .values(is_active=False)
                )

            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            await self.session.commit()
            await self.session.refresh(settings)
            return settings
        except ProviderSettingsNotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Provider settings integrity violation on update",
                provider_name=provider_name,
                exc_info=e,
            )
            raise DuplicateProviderSettingsError("fields", str(kwargs)) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error updating provider settings",
                provider_name=provider_name,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to update provider settings: {str(e)}") from e

    async def delete(self, provider_name: AIProvider) -> bool:
        try:
            settings = await self.get_by_provider(provider_name)
            if not settings:
                return False

            await self.session.delete(settings)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting provider settings",
                provider_name=provider_name,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete provider settings: {str(e)}") from e
