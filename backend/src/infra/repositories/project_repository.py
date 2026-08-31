import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.interfaces.ilogger import ILogger
from src.core.interfaces.iproject_repository import IProjectRepository
from src.core.exceptions.database import (
    RepositoryError,
    ProjectNotFoundError,
    DuplicateProjectError,
)
from src.models.project import Project


class ProjectRepository(IProjectRepository):
    """
    SQLAlchemy implementation of the IProjectRepository for PostgreSQL.
    """

    def __init__(self, session: AsyncSession, logger: ILogger) -> None:
        self.session = session
        self.logger = logger

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        try:
            stmt = select(Project).where(Project.project_id == project_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving project by ID",
                project_id=project_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve project: {str(e)}") from e

    async def get_by_doc_id(self, doc_id: uuid.UUID) -> Project | None:
        try:
            stmt = select(Project).where(Project.doc_id == doc_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error retrieving project by doc ID",
                doc_id=doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to retrieve project: {str(e)}") from e

    async def list_all(self, include_archived: bool = False) -> Sequence[Project]:
        try:
            stmt = select(Project)
            if not include_archived:
                stmt = stmt.where(Project.is_archived == False)
            stmt = stmt.order_by(Project.created_at.desc())
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            self.logger.error(
                "Database error listing projects",
                include_archived=include_archived,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to list projects: {str(e)}") from e

    async def create(self, project: Project) -> Project:
        try:
            self.session.add(project)
            await self.session.commit()
            await self.session.refresh(project)
            return project
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Project integrity violation on create",
                doc_id=project.doc_id,
                exc_info=e,
            )
            # If doc_id already exists since it is unique
            raise DuplicateProjectError("doc_id", project.doc_id) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error creating project",
                doc_id=project.doc_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to create project: {str(e)}") from e

    async def update(self, project_id: uuid.UUID, **kwargs) -> Project:
        try:
            project = await self.get_by_id(project_id)
            if not project:
                raise ProjectNotFoundError(project_id)

            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)

            await self.session.commit()
            await self.session.refresh(project)
            return project
        except ProjectNotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(
                "Project integrity violation on update",
                project_id=project_id,
                exc_info=e,
            )
            raise DuplicateProjectError("fields", str(kwargs)) from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error updating project",
                project_id=project_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to update project: {str(e)}") from e

    async def delete(self, project_id: uuid.UUID) -> bool:
        try:
            project = await self.get_by_id(project_id)
            if not project:
                return False

            await self.session.delete(project)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(
                "Database error deleting project",
                project_id=project_id,
                exc_info=e,
            )
            raise RepositoryError(f"Failed to delete project: {str(e)}") from e
