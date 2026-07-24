"""create tenancy and workspaces

Revision ID: e2f3a4b5c6d7
Revises: e1f2a3b4c5d6
Create Date: 2026-07-22 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 2. Create workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'], unique=False)

    # 3. Create workspace_members table
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='VIEWER'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_members_id'), 'workspace_members', ['id'], unique=False)

    # 4. Create workspace_invitations table
    op.create_table(
        'workspace_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('invited_by', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['invited_by'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspace_invitations_id'), 'workspace_invitations', ['id'], unique=False)

    # 5. Add workspace_id columns to existing tables
    op.add_column('documents', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.add_column('conversations', sa.Column('workspace_id', sa.Integer(), nullable=True))
    op.add_column('audit_logs', sa.Column('workspace_id', sa.Integer(), nullable=True))

    # Perform updates if there are any existing documents/conversations
    bind = op.get_bind()
    res = bind.execute(sa.text("SELECT id, username FROM accounts"))
    accounts = res.fetchall()
    
    if accounts:
        for acc in accounts:
            acc_id = acc[0]
            username = acc[1]
            org_slug = f"default-org-{acc_id}"
            
            # Insert organization
            bind.execute(sa.text(
                f"INSERT INTO organizations (name, slug, owner_id, created_at, updated_at) "
                f"VALUES ('Default Org', '{org_slug}', {acc_id}, NOW(), NOW())"
            ))
            
            # Fetch organization id
            org_res = bind.execute(sa.text(f"SELECT id FROM organizations WHERE slug = '{org_slug}'"))
            org_id = org_res.scalar()
            
            # Insert workspace
            bind.execute(sa.text(
                f"INSERT INTO workspaces (organization_id, name, description, created_at, updated_at) "
                f"VALUES ({org_id}, 'Personal Workspace', 'Default personal workspace', NOW(), NOW())"
            ))
            
            # Fetch workspace id
            ws_res = bind.execute(sa.text(f"SELECT id FROM workspaces WHERE organization_id = {org_id}"))
            ws_id = ws_res.scalar()
            
            # Insert membership
            bind.execute(sa.text(
                f"INSERT INTO workspace_members (workspace_id, account_id, role, joined_at) "
                f"VALUES ({ws_id}, {acc_id}, 'OWNER', NOW())"
            ))
            
            # Update existing documents for this user
            bind.execute(sa.text(f"UPDATE documents SET workspace_id = {ws_id} WHERE account_id = {acc_id}"))
            
            # Update existing conversations for this user
            bind.execute(sa.text(f"UPDATE conversations SET workspace_id = {ws_id} WHERE account_id = {acc_id}"))
            
            # Update existing audit logs for this user
            bind.execute(sa.text(f"UPDATE audit_logs SET workspace_id = {ws_id} WHERE account_id = {acc_id}"))
            
    # 6. Now alter columns to nullable=False for documents and conversations
    # If no accounts exist but documents exist (very unlikely), we set to 1 or default
    bind.execute(sa.text("UPDATE documents SET workspace_id = 1 WHERE workspace_id IS NULL"))
    bind.execute(sa.text("UPDATE conversations SET workspace_id = 1 WHERE workspace_id IS NULL"))
    
    op.alter_column('documents', 'workspace_id', nullable=False)
    op.alter_column('conversations', 'workspace_id', nullable=False)

    # 7. Add foreign keys and indexes
    op.create_foreign_key('fk_documents_workspace_id', 'documents', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_documents_workspace_id'), 'documents', ['workspace_id'], unique=False)

    op.create_foreign_key('fk_conversations_workspace_id', 'conversations', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_conversations_workspace_id'), 'conversations', ['workspace_id'], unique=False)

    op.create_foreign_key('fk_audit_logs_workspace_id', 'audit_logs', 'workspaces', ['workspace_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_audit_logs_workspace_id'), 'audit_logs', ['workspace_id'], unique=False)

def downgrade() -> None:
    # Remove indexes and foreign keys
    op.drop_index(op.f('ix_audit_logs_workspace_id'), table_name='audit_logs')
    op.drop_constraint('fk_audit_logs_workspace_id', 'audit_logs', type_='foreignkey')
    op.drop_column('audit_logs', 'workspace_id')

    op.drop_index(op.f('ix_conversations_workspace_id'), table_name='conversations')
    op.drop_constraint('fk_conversations_workspace_id', 'conversations', type_='foreignkey')
    op.drop_column('conversations', 'workspace_id')

    op.drop_index(op.f('ix_documents_workspace_id'), table_name='documents')
    op.drop_constraint('fk_documents_workspace_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'workspace_id')

    # Drop tables
    op.drop_index(op.f('ix_workspace_invitations_id'), table_name='workspace_invitations')
    op.drop_table('workspace_invitations')

    op.drop_index(op.f('ix_workspace_members_id'), table_name='workspace_members')
    op.drop_table('workspace_members')

    op.drop_index(op.f('ix_workspaces_id'), table_name='workspaces')
    op.drop_table('workspaces')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_index(op.f('ix_organizations_id'), table_name='organizations')
    op.drop_table('organizations')
