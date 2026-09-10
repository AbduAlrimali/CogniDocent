import uuid
from src.models.embedding_index_metadata import EmbeddingIndexMetadata
from src.models.project import Project


def test_embedding_index_metadata_creation():
    project_id = uuid.uuid4()
    meta = EmbeddingIndexMetadata(
        project_id=project_id,
        active_model="text-embedding-3-small",
        dimensions=1536,
    )
    assert meta.project_id == project_id
    assert meta.active_model == "text-embedding-3-small"
    assert meta.dimensions == 1536
    assert "EmbeddingIndexMetadata" in repr(meta)
    assert "text-embedding-3-small" in repr(meta)


def test_project_embedding_metadata_relationship():
    project = Project(
        project_id=uuid.uuid4(),
        doc_id=uuid.uuid4(),
        title="Test Project",
    )
    meta = EmbeddingIndexMetadata(
        project_id=project.project_id,
        active_model="nomic-embed-text-v2-moe",
        dimensions=768,
        project=project,
    )
    assert meta.project == project
    assert meta.active_model == "nomic-embed-text-v2-moe"
    assert meta.dimensions == 768
