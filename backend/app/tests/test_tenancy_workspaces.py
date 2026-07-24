import sys
from unittest.mock import MagicMock, AsyncMock, patch
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["chromadb"] = MagicMock()

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_account
from app.models.account import Account
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.workspace_invitation import WorkspaceInvitation
from app.tenancy.tenant_context import TenantContext
from app.tenancy.tenant_guard import get_tenant_context
from app.organizations.organization_service import OrganizationService
from app.workspaces.workspace_service import WorkspaceService
from app.workspaces.membership_service import MembershipService
from app.organizations.invitation_service import InvitationService

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_account():
    acc = Account()
    acc.id = 1
    acc.username = "workspace_owner"
    acc.email = "owner@aegis.ai"
    acc.is_active = True
    return acc

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    
    async def mock_refresh(instance):
        if hasattr(instance, "id") and not instance.id:
            instance.id = 1
        if hasattr(instance, "created_at") and not instance.created_at:
            instance.created_at = datetime.now(timezone.utc)
        if hasattr(instance, "updated_at") and not instance.updated_at:
            instance.updated_at = datetime.now(timezone.utc)
            
    db.refresh = mock_refresh
    db.delete = AsyncMock()
    return db

# -------------------------------------------------------------
# 1. Organization & Workspace Provisioning Checks
# -------------------------------------------------------------

@pytest.mark.anyio
async def test_create_organization_provisions_default_workspace(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.side_effect = [1, 2]
    
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    with patch("app.audit.audit_service.AuditService.log_event", new_callable=AsyncMock) as mock_audit:
        org = await OrganizationService.create_organization(
            db=mock_db,
            name="Aegis Enterprise",
            owner_id=1
        )
        
        assert org is not None
        assert org.name == "Aegis Enterprise"
        assert org.slug == "aegis-enterprise"
        assert org.owner_id == 1
        assert mock_audit.called is True

# -------------------------------------------------------------
# 2. Quota Enforcements (Workspaces & Members)
# -------------------------------------------------------------

@pytest.mark.anyio
async def test_workspace_quota_limit(mock_db):
    from app.config.settings import settings
    with patch.object(settings, "MAX_WORKSPACES_PER_ORGANIZATION", 2):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError) as exc:
            await WorkspaceService.create_workspace(
                db=mock_db,
                organization_id=1,
                name="Overflow WS",
                description=None,
                creator_id=1
            )
        assert "maximum quota of 2 workspaces" in str(exc.value)

@pytest.mark.anyio
async def test_member_quota_limit(mock_db):
    from app.config.settings import settings
    with patch.object(settings, "MAX_MEMBERS_PER_WORKSPACE", 2):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError) as exc:
            await MembershipService.add_member(
                db=mock_db,
                workspace_id=1,
                account_id=3,
                role="VIEWER",
                actor_id=1
            )
        assert "maximum allowed limit of 2 members" in str(exc.value)

# -------------------------------------------------------------
# 3. Invitation Acceptance Flow
# -------------------------------------------------------------

@pytest.mark.anyio
async def test_accept_invitation_flow(mock_db):
    invite = WorkspaceInvitation()
    invite.id = 1
    invite.workspace_id = 1
    invite.email = "invitee@corporate.com"
    invite.status = "PENDING"
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    
    acc = Account()
    acc.id = 2
    acc.email = "invitee@corporate.com"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.side_effect = [invite, acc, None]
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    with patch("app.workspaces.membership_service.MembershipService.add_member", new_callable=AsyncMock) as mock_add_member:
        success = await InvitationService.accept_invitation(
            db=mock_db,
            invitation_id=1,
            account_id=2
        )
        assert success is True
        assert invite.status == "ACCEPTED"
        assert mock_add_member.called is True

# -------------------------------------------------------------
# 4. API Route Permissions Check
# -------------------------------------------------------------

def test_api_requires_workspace_header(mock_account):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    response = client.get("/api/v1/workspaces/1")
    assert response.status_code == 400
    assert "Missing X-Workspace-ID header" in response.json()["detail"]

def test_api_workspace_forbidden_for_non_members(mock_account):
    app.dependency_overrides[get_current_account] = lambda: mock_account
    
    from fastapi import HTTPException
    async def mock_get_tenant_context():
        raise HTTPException(status_code=403, detail="Access Denied: You are not a member of this workspace.")
        
    app.dependency_overrides[get_tenant_context] = mock_get_tenant_context
    
    response = client.get("/api/v1/workspaces/1", headers={"X-Workspace-ID": "1"})
    assert response.status_code == 403
