"""add rich metadata to document chunks

Revision ID: f1a2b3c4d5e6
Revises: c1d2e3f4a5b6
Create Date: 2026-07-24 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rich semantic metadata columns to document_chunks table for enterprise RAG."""
    op.add_column('document_chunks', sa.Column('section', sa.String(512), nullable=True))
    op.add_column('document_chunks', sa.Column('heading', sa.String(512), nullable=True))
    op.add_column('document_chunks', sa.Column('topic', sa.String(255), nullable=True))
    op.add_column('document_chunks', sa.Column('keywords', sa.Text(), nullable=True))
    op.add_column('document_chunks', sa.Column('hierarchy_level', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('chunk_type', sa.String(50), nullable=True, server_default='paragraph'))

    # Index on section for metadata filtering
    op.create_index(
        'ix_document_chunks_section',
        'document_chunks',
        ['section'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_document_chunks_section', table_name='document_chunks')
    op.drop_column('document_chunks', 'chunk_type')
    op.drop_column('document_chunks', 'hierarchy_level')
    op.drop_column('document_chunks', 'keywords')
    op.drop_column('document_chunks', 'topic')
    op.drop_column('document_chunks', 'heading')
    op.drop_column('document_chunks', 'section')
