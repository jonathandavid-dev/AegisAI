import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';

export interface Organization {
  id: number;
  name: string;
  slug: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface Workspace {
  id: number;
  organization_id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  account_id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  joined_at: string;
}

export interface WorkspaceInvitation {
  id: number;
  workspace_id: number;
  email: string;
  status: string;
  expires_at: string;
}

interface WorkspaceContextType {
  activeOrganization: Organization | null;
  activeWorkspace: Workspace | null;
  organizations: Organization[];
  workspaces: Workspace[];
  members: WorkspaceMember[];
  invitations: WorkspaceInvitation[];
  loading: boolean;
  switchOrganization: (orgId: number) => Promise<void>;
  switchWorkspace: (workspaceId: number) => void;
  createOrganization: (name: string) => Promise<Organization>;
  createWorkspace: (name: string, description?: string) => Promise<Workspace>;
  inviteMember: (email: string) => Promise<void>;
  removeMember: (accountId: number) => Promise<void>;
  updateMemberRole: (accountId: number, role: string) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
  refreshWorkspaces: () => Promise<void>;
  refreshMembers: () => Promise<void>;
  refreshInvitations: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeOrganization, setActiveOrganization] = useState<Organization | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshOrganizations = async () => {
    try {
      const response = await api.get('/organizations');
      setOrganizations(response.data);
      if (response.data.length > 0) {
        const savedOrgId = localStorage.getItem('aegis_active_org_id');
        const active = response.data.find((o: Organization) => o.id.toString() === savedOrgId) || response.data[0];
        setActiveOrganization(active);
        localStorage.setItem('aegis_active_org_id', active.id.toString());
      } else {
        setActiveOrganization(null);
        setWorkspaces([]);
        setActiveWorkspace(null);
      }
    } catch (err) {
      console.error('Failed to load organizations', err);
    }
  };

  const refreshWorkspaces = async () => {
    if (!activeOrganization) return;
    try {
      const response = await api.get(`/workspaces?organization_id=${activeOrganization.id}`);
      setWorkspaces(response.data);
      if (response.data.length > 0) {
        const savedWsId = localStorage.getItem('aegis_active_workspace_id');
        const active = response.data.find((w: Workspace) => w.id.toString() === savedWsId) || response.data[0];
        setActiveWorkspace(active);
        localStorage.setItem('aegis_active_workspace_id', active.id.toString());
      } else {
        setActiveWorkspace(null);
        localStorage.removeItem('aegis_active_workspace_id');
      }
    } catch (err) {
      console.error('Failed to load workspaces', err);
    }
  };

  const refreshMembers = async () => {
    if (!activeWorkspace) return;
    try {
      const response = await api.get(`/workspaces/${activeWorkspace.id}/members`);
      setMembers(response.data);
      if (user) {
        const me = response.data.find((m: any) => m.account_id === user.id);
        if (me) {
          localStorage.setItem('aegis_workspace_role', me.role);
        }
      }
    } catch (err) {
      console.error('Failed to load workspace members', err);
    }
  };

  const refreshInvitations = async () => {
    if (!activeWorkspace) return;
    try {
      const response = await api.get(`/workspaces/${activeWorkspace.id}/invitations`);
      setInvitations(response.data);
    } catch (err) {
      console.error('Failed to load workspace invitations', err);
    }
  };

  useEffect(() => {
    const initialize = async () => {
      setLoading(true);
      await refreshOrganizations();
      setLoading(false);
    };
    if (localStorage.getItem('aegis_token') && user) {
      initialize();
    }
  }, [user]);

  useEffect(() => {
    if (activeOrganization) {
      refreshWorkspaces();
    }
  }, [activeOrganization]);

  useEffect(() => {
    if (activeWorkspace) {
      refreshMembers();
      refreshInvitations();
    } else {
      setMembers([]);
      setInvitations([]);
    }
  }, [activeWorkspace]);

  const switchOrganization = async (orgId: number) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) {
      setActiveOrganization(org);
      localStorage.setItem('aegis_active_org_id', orgId.toString());
      localStorage.removeItem('aegis_active_workspace_id');
    }
  };

  const switchWorkspace = (workspaceId: number) => {
    const ws = workspaces.find((w) => w.id === workspaceId);
    if (ws) {
      setActiveWorkspace(ws);
      localStorage.setItem('aegis_active_workspace_id', workspaceId.toString());
    }
  };

  const createOrganization = async (name: string) => {
    const response = await api.post('/organizations', { name });
    const newOrg = response.data;
    setOrganizations((prev) => [...prev, newOrg]);
    setActiveOrganization(newOrg);
    localStorage.setItem('aegis_active_org_id', newOrg.id.toString());
    localStorage.removeItem('aegis_active_workspace_id');
    return newOrg;
  };

  const createWorkspace = async (name: string, description?: string) => {
    if (!activeOrganization) throw new Error('No active organization');
    const response = await api.post(`/workspaces?organization_id=${activeOrganization.id}`, { name, description });
    const newWs = response.data;
    setWorkspaces((prev) => [...prev, newWs]);
    setActiveWorkspace(newWs);
    localStorage.setItem('aegis_active_workspace_id', newWs.id.toString());
    return newWs;
  };

  const inviteMember = async (email: string) => {
    if (!activeWorkspace) throw new Error('No active workspace');
    await api.post(`/workspaces/${activeWorkspace.id}/invitations`, { email });
    await refreshInvitations();
  };

  const removeMember = async (accountId: number) => {
    if (!activeWorkspace) throw new Error('No active workspace');
    await api.delete(`/workspaces/${activeWorkspace.id}/members/${accountId}`);
    await refreshMembers();
  };

  const updateMemberRole = async (accountId: number, role: string) => {
    if (!activeWorkspace) throw new Error('No active workspace');
    await api.patch(`/workspaces/${activeWorkspace.id}/members/${accountId}`, { role });
    await refreshMembers();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        activeOrganization,
        activeWorkspace,
        organizations,
        workspaces,
        members,
        invitations,
        loading,
        switchOrganization,
        switchWorkspace,
        createOrganization,
        createWorkspace,
        inviteMember,
        removeMember,
        updateMemberRole,
        refreshOrganizations,
        refreshWorkspaces,
        refreshMembers,
        refreshInvitations,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
