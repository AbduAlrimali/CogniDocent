from abc import ABC, abstractmethod
import uuid
from typing import Sequence
from src.models.project import Project


class IProjectRepository(ABC):
    """
    Interface for Project repository operations (Port).
    """

    @abstractmethod
    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        """
        Retrieve a project by its ID.
        """
        pass

    @abstractmethod
    async def get_by_doc_id(self, doc_id: uuid.UUID) -> Project | None:
        """
        Retrieve a project by its associated Document ID (doc_id).
        """
        pass

    @abstractmethod
    async def list_all(self, include_archived: bool = False) -> Sequence[Project]:
        """
        Retrieve a list of all projects.
        """
        pass

    @abstractmethod
    async def create(self, project: Project) -> Project:
        """
        Save a new project to the database.
        """
        pass

    @abstractmethod
    async def update(self, project_id: uuid.UUID, **kwargs) -> Project:
        """
        Update fields of an existing project.
        """
        pass

    @abstractmethod
    async def delete(self, project_id: uuid.UUID) -> bool:
        """
        Delete a project by its ID. Returns True if deleted.
        """
        pass
