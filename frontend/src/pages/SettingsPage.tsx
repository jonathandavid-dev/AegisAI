import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Settings, Shield, User, Key, Eye, EyeOff } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [showToken, setShowToken] = useState(false);
  const token = localStorage.getItem('aegis_token') || 'No active session token found';

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary">
          <Settings className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">System Settings</h1>
          <p className="text-sm text-gray-400">Manage user configuration parameters and inspect current token parameters.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Account Details */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card">
            <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <User className="w-4 h-4 text-brand-primary" /> Profile Credentials
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
              <div className="space-y-1">
                <span className="text-xs text-gray-400 block font-semibold uppercase tracking-wider">Username</span>
                <input
                  type="text"
                  disabled
                  value={user?.username || ''}
                  className="w-full glass-input bg-brand-background/25 border-brand-border/40 opacity-70 cursor-not-allowed"
                />
              </div>
              <div className="space-y-1">
                <span className="text-xs text-gray-400 block font-semibold uppercase tracking-wider">Email Address</span>
                <input
                  type="text"
                  disabled
                  value={user?.email || ''}
                  className="w-full glass-input bg-brand-background/25 border-brand-border/40 opacity-70 cursor-not-allowed"
                />
              </div>
              <div className="space-y-1">
                <span className="text-xs text-gray-400 block font-semibold uppercase tracking-wider">Account ID</span>
                <input
                  type="text"
                  disabled
                  value={user?.id || ''}
                  className="w-full glass-input bg-brand-background/25 border-brand-border/40 opacity-70 cursor-not-allowed"
                />
              </div>
              <div className="space-y-1">
                <span className="text-xs text-gray-400 block font-semibold uppercase tracking-wider">Status State</span>
                <div className="w-full glass-input bg-brand-background/25 border-brand-border/40 opacity-70 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-green-400" /> Active Enterprise User
                </div>
              </div>
            </div>
          </div>

          {/* Session Token Inspector */}
          <div className="glass-card">
            <h2 className="text-base font-semibold text-white mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Key className="w-4 h-4 text-brand-accent" /> JWT Access Token Inspector
              </span>
              <button
                onClick={() => setShowToken(!showToken)}
                className="text-xs text-brand-primary hover:text-brand-accent flex items-center gap-1.5 focus:outline-none"
              >
                {showToken ? (
                  <>
                    <EyeOff className="w-3.5 h-3.5" /> Mask Token
                  </>
                ) : (
                  <>
                    <Eye className="w-3.5 h-3.5" /> Inspect Token
                  </>
                )}
              </button>
            </h2>
            <p className="text-xs text-gray-400 mb-4 leading-relaxed">
              This signature token is appended automatically inside the headers of Axios network requests.
            </p>
            <div className="p-4 rounded-lg bg-brand-background/50 border border-brand-border/60">
              <span className="font-mono text-xs break-all block text-brand-accent/90">
                {showToken ? token : '••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••'}
              </span>
            </div>
          </div>
        </div>

        {/* Configurations Column */}
        <div className="glass-card">
          <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-400" /> Security Settings
          </h2>
          <div className="space-y-4 text-sm text-gray-400">
            <div className="flex justify-between items-center py-2 border-b border-brand-border/40">
              <span>Token Expiration</span>
              <span className="font-mono text-xs text-white">60 Minutes</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-brand-border/40">
              <span>Hashing Mechanism</span>
              <span className="font-mono text-xs text-white">bcrypt</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-brand-border/40">
              <span>Signature Crypt</span>
              <span className="font-mono text-xs text-white">HS256</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span>Cors Allowed Origins</span>
              <span className="font-mono text-[10px] text-white bg-brand-border/60 px-1 rounded">All (*)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export type email = string;
