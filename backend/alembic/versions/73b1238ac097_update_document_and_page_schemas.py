"""update_document_and_page_schemas

Revision ID: 73b1238ac097
Revises: 19fdb92be172
Create Date: 2026-09-11 18:14:02.779154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = "73b1238ac097"
down_revision: Union[str, Sequence[str], None] = "19fdb92be172"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Update documents table
    op.add_column("documents", sa.Column("toc", sa.JSON(), nullable=True, comment="Extracted table of contents / bookmarks stored as JSON"))
    op.add_column("documents", sa.Column("metadata", sa.JSON(), nullable=True, comment="Document header metadata stored as JSON"))

    # 2. Update document_pages table
    # Drop legacy indexes if they exist
    op.execute("DROP INDEX IF EXISTS idx_document_pages_search_vector;")
    op.execute("DROP INDEX IF EXISTS idx_document_pages_embedding;")

    # Drop legacy columns
    op.execute("ALTER TABLE document_pages DROP COLUMN IF EXISTS search_vector;")
    op.execute("ALTER TABLE document_pages DROP COLUMN IF EXISTS metadata;")
    op.execute("ALTER TABLE document_pages DROP COLUMN IF EXISTS markdown_content;")
    op.execute("ALTER TABLE document_pages DROP COLUMN IF EXISTS embedding;")

    # Add new columns
    op.add_column("document_pages", sa.Column("content_vector", Vector(768), nullable=True))
    op.add_column("document_pages", sa.Column("deep_content", sa.Text(), nullable=True))
    op.add_column("document_pages", sa.Column("deep_content_vector", Vector(768), nullable=True))

    # Add HNSW indexes for vector search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_pages_content_vector
        ON document_pages USING hnsw (content_vector vector_cosine_ops);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_pages_deep_content_vector
        ON document_pages USING hnsw (deep_content_vector vector_cosine_ops);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_document_pages_deep_content_vector;")
    op.execute("DROP INDEX IF EXISTS idx_document_pages_content_vector;")

    op.drop_column("document_pages", "deep_content_vector")
    op.drop_column("document_pages", "deep_content")
    op.drop_column("document_pages", "content_vector")

    op.add_column("document_pages", sa.Column("embedding", Vector(768), nullable=True))
    op.add_column("document_pages", sa.Column("markdown_content", sa.Text(), nullable=True))
    op.add_column("document_pages", sa.Column("metadata", sa.JSON(), nullable=True))

    op.drop_column("documents", "metadata")
    op.drop_column("documents", "toc")
