import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useWorkspace } from '../context/WorkspaceContext';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, User, LogOut, Settings, ChevronDown, Plus, Globe, Check, Users } from 'lucide-react';
import { Avatar, Button, Input } from './ui/Primitives';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { 
    activeOrganization, 
    activeWorkspace, 
    organizations, 
    workspaces, 
    switchOrganization, 
    switchWorkspace,
    createWorkspace
  } = useWorkspace();

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [wsDropdownOpen, setWsDropdownOpen] = useState(false);
  const [showCreateWs, setShowCreateWs] = useState(false);
  const [newWsName, setNewWsName] = useState('');
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const wsRole = localStorage.getItem('aegis_workspace_role') || 'OWNER';

  return (
    <nav className="h-16 border-b border-brand-border/40 bg-brand-surface/40 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6 text-brand-accent animate-pulse" />
        <span className="font-extrabold text-xl tracking-wider bg-gradient-to-r from-white via-[#E5E7EB] to-brand-accent bg-clip-text text-transparent">
          AegisAI
        </span>
        <span className="hidden md:inline text-[9px] text-brand-accent/80 border border-brand-accent/30 rounded px-1.5 py-0.5 uppercase tracking-widest font-mono font-semibold">
          Enterprise
        </span>
        
        {/* Workspace Switcher */}
        {activeWorkspace && (
          <div className="relative ml-4">
            <button
              onClick={() => setWsDropdownOpen(!wsDropdownOpen)}
              className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold text-brand-textSecondary hover:text-white bg-[#0D0D0D]/40 border border-brand-border hover:border-brand-primary/40 rounded-xl transition-all select-none cursor-pointer"
            >
              <Globe className="w-3.5 h-3.5 text-brand-accent" />
              <span>{activeOrganization?.name} / {activeWorkspace?.name}</span>
              <ChevronDown className="w-3.5 h-3.5 text-brand-textMuted" />
            </button>
            
            {wsDropdownOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setWsDropdownOpen(false)} />
                <div className="absolute left-0 mt-2 w-64 bg-brand-surface border border-brand-border rounded-xl shadow-2xl p-2 z-20 animate-scale-up text-left">
                  <div className="px-2.5 py-1.5 text-[9px] font-mono text-brand-textMuted uppercase tracking-wider">Organizations</div>
                  {organizations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => { switchOrganization(org.id); setWsDropdownOpen(false); }}
                      className="w-full flex items-center justify-between px-3 py-1.5 text-xs text-brand-textSecondary hover:text-white hover:bg-brand-primary/10 rounded-lg transition-colors text-left cursor-pointer"
                    >
                      <span>{org.name}</span>
                      {activeOrganization?.id === org.id && <Check className="w-3.5 h-3.5 text-brand-accent" />}
                    </button>
                  ))}
                  
                  <div className="border-t border-brand-border/40 my-2" />
                  
                  <div className="px-2.5 py-1.5 text-[9px] font-mono text-brand-textMuted uppercase tracking-wider">Workspaces</div>
                  {workspaces.map((ws) => (
                    <button
                      key={ws.id}
                      onClick={() => { switchWorkspace(ws.id); setWsDropdownOpen(false); }}
                      className="w-full flex items-center justify-between px-3 py-1.5 text-xs text-brand-textSecondary hover:text-white hover:bg-brand-primary/10 rounded-lg transition-colors text-left cursor-pointer"
                    >
                      <span>{ws.name}</span>
                      {activeWorkspace?.id === ws.id && <Check className="w-3.5 h-3.5 text-brand-accent" />}
                    </button>
                  ))}
                  
                  <div className="border-t border-brand-border/40 my-2" />
                  
                  <button
                    onClick={() => { setWsDropdownOpen(false); setShowCreateWs(true); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-brand-accent hover:bg-brand-accent/10 rounded-lg transition-colors text-left cursor-pointer"
                  >
                    <Plus className="w-4 h-4" /> Create Workspace...
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="relative">
            <div 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-3 cursor-pointer hover:opacity-90 select-none p-1.5 rounded-xl hover:bg-white/5 transition-colors"
            >
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-bold text-brand-text leading-tight">{user.full_name || user.username}</span>
                <span className="text-[9px] text-brand-textMuted font-mono leading-none mt-0.5">
                  {user.role} {activeWorkspace && `| ${wsRole}`}
                </span>
              </div>
              <Avatar name={user.full_name || user.username} size="sm" />
              <ChevronDown className="w-3.5 h-3.5 text-brand-textMuted" />
            </div>

            {dropdownOpen && (
              <>
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setDropdownOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-48 bg-brand-surface border border-brand-border rounded-xl shadow-2xl p-1.5 z-20 animate-scale-up font-sans">
                  <Link 
                    to="/profile" 
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-brand-textSecondary hover:text-white hover:bg-brand-primary/10 rounded-lg transition-colors"
                  >
                    <User className="w-4 h-4 text-brand-primary" /> Profile Page
                  </Link>
                  <Link 
                    to="/settings" 
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-brand-textSecondary hover:text-white hover:bg-brand-primary/10 rounded-lg transition-colors"
                  >
                    <Settings className="w-4 h-4 text-brand-primary" /> System Settings
                  </Link>
                  <Link 
                    to="/settings/workspace" 
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-brand-textSecondary hover:text-white hover:bg-brand-primary/10 rounded-lg transition-colors"
                  >
                    <Users className="w-4 h-4 text-brand-primary" /> Team Members
                  </Link>
                  <div className="border-t border-brand-border/40 my-1" />
                  <button 
                    onClick={() => { setDropdownOpen(false); handleLogout(); }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/10 rounded-lg transition-colors text-left cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" /> Sign Out
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {showCreateWs && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-brand-surface border border-brand-border rounded-2xl p-6 w-full max-w-md shadow-2xl animate-fade-in text-left">
            <h3 className="text-sm font-bold text-white mb-1">Create Workspace</h3>
            <p className="text-xs text-brand-textSecondary mb-4">Enter a name for your new workspace project layer.</p>
            <Input
              type="text"
              placeholder="Workspace Name"
              value={newWsName}
              onChange={(e) => setNewWsName(e.target.value)}
              className="mb-4"
            />
            <div className="flex justify-end gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => { setShowCreateWs(false); setNewWsName(''); }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={async () => {
                  if (newWsName.trim()) {
                    await createWorkspace(newWsName);
                    setShowCreateWs(false);
                    setNewWsName('');
                  }
                }}
              >
                Create
              </Button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};
