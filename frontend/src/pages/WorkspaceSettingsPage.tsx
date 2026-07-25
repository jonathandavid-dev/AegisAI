import React, { useState } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { useAuth } from '../hooks/useAuth';
import { Users, Mail, Trash2, UserPlus, UserCheck, ShieldAlert } from 'lucide-react';
import { Card, Button, Input, Badge } from '../components/ui/Primitives';

export const WorkspaceSettingsPage: React.FC = () => {
  const { activeWorkspace, members, invitations, inviteMember, removeMember, updateMemberRole } = useWorkspace();
  const { user } = useAuth();
  const [inviteEmail, setInviteEmail] = useState('');
  const [loadingInvite, setLoadingInvite] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const currentRole = localStorage.getItem('aegis_workspace_role') || 'VIEWER';
  const isOwnerOrAdmin = ['OWNER', 'ADMIN'].includes(currentRole.toUpperCase());

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setLoadingInvite(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      await inviteMember(inviteEmail);
      setSuccessMsg(`Successfully sent invitation to ${inviteEmail}`);
      setInviteEmail('');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setLoadingInvite(false);
    }
  };

  const handleRoleChange = async (accountId: number, role: string) => {
    try {
      await updateMemberRole(accountId, role);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update member role');
    }
  };

  const handleRemove = async (accountId: number) => {
    if (!window.confirm('Are you sure you want to remove this member?')) return;
    try {
      await removeMember(accountId);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  if (!activeWorkspace) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 bg-brand-background text-brand-textMuted font-sans">
        No active workspace loaded. Please select a workspace.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-brand-background font-sans select-none animate-fade-in-up">
      <div className="max-w-4xl mx-auto space-y-8">
        
        <div className="border-b border-brand-border/40 pb-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-extrabold text-white flex items-center gap-2.5">
              <Users className="w-5.5 h-5.5 text-brand-primary" /> Workspace Management
            </h1>
            <p className="text-xs text-brand-textSecondary mt-1">
              Manage users, pending invitations, and authorization scopes for workspace "{activeWorkspace.name}".
            </p>
          </div>
        </div>

        {isOwnerOrAdmin && (
          <Card className="p-6" glow>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <Mail className="w-4 h-4 text-brand-primary" /> Invite Team Member
            </h3>
            <p className="text-xs text-brand-textSecondary mb-4">
              Enter an email address to invite a colleague to join this collaborative workspace as a viewer.
            </p>
            <form onSubmit={handleInvite} className="flex gap-3">
              <Input
                type="email"
                required
                placeholder="colleague@enterprise.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
              <Button
                type="submit"
                disabled={loadingInvite}
                className="text-xs font-bold shrink-0"
              >
                <UserPlus className="w-4 h-4" /> Send Invite
              </Button>
            </form>
            {successMsg && <p className="text-xs text-green-400 mt-3 font-semibold">{successMsg}</p>}
            {errorMsg && <p className="text-xs text-red-400 mt-3 font-semibold">{errorMsg}</p>}
          </Card>
        )}

        <Card className="p-6" glow>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-brand-accent" /> Enrolled Team Members
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-brand-border/60 text-brand-textMuted">
                  <th className="pb-3 font-bold uppercase tracking-wider">User</th>
                  <th className="pb-3 font-bold uppercase tracking-wider">Email</th>
                  <th className="pb-3 font-bold uppercase tracking-wider">Workspace Role</th>
                  {isOwnerOrAdmin && <th className="pb-3 font-bold uppercase tracking-wider text-right">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/40">
                {members.map((member) => (
                  <tr key={member.account_id} className="text-brand-textSecondary hover:bg-brand-surface/20 transition-colors">
                    <td className="py-4 font-bold text-white flex items-center">
                      {member.full_name || member.username}
                      {member.account_id === user?.id && (
                        <Badge variant="primary" className="ml-2 py-0 px-1.5 text-[8px]">
                          You
                        </Badge>
                      )}
                    </td>
                    <td className="py-4 font-mono text-[10px]">{member.email}</td>
                    <td className="py-4">
                      {isOwnerOrAdmin && member.account_id !== user?.id ? (
                        <select
                          value={member.role}
                          onChange={(e) => handleRoleChange(member.account_id, e.target.value)}
                          className="bg-brand-background border border-brand-border rounded-xl px-2.5 py-1 text-xs text-white focus:outline-none focus:border-brand-primary"
                        >
                          <option value="OWNER" className="bg-[#111827]">OWNER</option>
                          <option value="ADMIN" className="bg-[#111827]">ADMIN</option>
                          <option value="EDITOR" className="bg-[#111827]">EDITOR</option>
                          <option value="VIEWER" className="bg-[#111827]">VIEWER</option>
                        </select>
                      ) : (
                        <Badge variant="secondary">{member.role}</Badge>
                      )}
                    </td>
                    {isOwnerOrAdmin && (
                      <td className="py-4 text-right">
                        {member.account_id !== user?.id && (
                          <button
                            onClick={() => handleRemove(member.account_id)}
                            className="text-red-400 hover:text-red-300 p-1 transition-colors cursor-pointer"
                            title="Remove Member"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {invitations.length > 0 && (
          <Card className="p-6" glow>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-brand-primary" /> Pending Invitations
            </h3>
            <div className="space-y-3">
              {invitations.map((invite) => (
                <div 
                  key={invite.id}
                  className="flex items-center justify-between p-3.5 bg-brand-background/40 border border-brand-border/60 rounded-xl"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary shrink-0">
                      <Mail className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-white">{invite.email}</p>
                      <p className="text-[9px] text-brand-textMuted font-mono mt-0.5">
                        Expires: {new Date(invite.expires_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-[8px]">
                    {invite.status}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
export default WorkspaceSettingsPage;
