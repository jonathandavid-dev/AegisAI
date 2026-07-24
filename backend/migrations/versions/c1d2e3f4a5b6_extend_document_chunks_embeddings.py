"""extend document chunks embeddings

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-07-22 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Define ChunkEmbeddingStatus enum type
    chunk_embedding_status_enum = sa.Enum(
        'PENDING', 'PROCESSING', 'INDEXED', 'FAILED', 
        name='chunk_embedding_status_enum'
    )
    chunk_embedding_status_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Add columns
    op.add_column('document_chunks', sa.Column(
        'embedding_status', 
        chunk_embedding_status_enum, 
        nullable=False, 
        server_default='PENDING'
    ))
    op.add_column('document_chunks', sa.Column(
        'embedded_at', 
        sa.DateTime(timezone=True), 
        nullable=True
    ))
    
    # 3. Create index on embedding_status
    op.create_index(
        op.f('ix_document_chunks_embedding_status'), 
        'document_chunks', 
        ['embedding_status'], 
        unique=False
    )

def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunks_embedding_status'), table_name='document_chunks')
    op.drop_column('document_chunks', 'embedded_at')
    op.drop_column('document_chunks', 'embedding_status')
    
    # Drop Enum type
    chunk_embedding_status_enum = sa.Enum(name='chunk_embedding_status_enum')
    chunk_embedding_status_enum.drop(op.get_bind(), checkfirst=True)
