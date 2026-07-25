import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Settings, Shield, User, Key, Eye, EyeOff } from 'lucide-react';
import { Card, Button, Input, Badge } from '../components/ui/Primitives';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [showToken, setShowToken] = useState(false);
  const token = localStorage.getItem('aegis_token') || 'No active session token found';

  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-fade-in-up">
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary shadow-[0_0_15px_rgba(16,185,129,0.08)]">
            <Settings className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white">System Settings</h1>
            <p className="text-xs text-brand-textSecondary">Manage user configuration parameters and inspect current token parameters.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Account Details */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6" glow>
            <h2 className="text-xs font-bold text-white mb-6 uppercase tracking-wider flex items-center gap-2">
              <User className="w-4 h-4 text-brand-primary" /> Profile Credentials
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
              <div className="space-y-1.5">
                <span className="text-[10px] text-brand-textMuted block font-bold uppercase tracking-wider font-mono">Username</span>
                <Input
                  type="text"
                  disabled
                  value={user?.username || ''}
                  className="bg-brand-background/20 opacity-70 cursor-not-allowed select-none"
                />
              </div>
              <div className="space-y-1.5">
                <span className="text-[10px] text-brand-textMuted block font-bold uppercase tracking-wider font-mono">Email Address</span>
                <Input
                  type="text"
                  disabled
                  value={user?.email || ''}
                  className="bg-brand-background/20 opacity-70 cursor-not-allowed select-none"
                />
              </div>
              <div className="space-y-1.5">
                <span className="text-[10px] text-brand-textMuted block font-bold uppercase tracking-wider font-mono">Account ID</span>
                <Input
                  type="text"
                  disabled
                  value={user?.id || ''}
                  className="bg-brand-background/20 opacity-70 cursor-not-allowed select-none"
                />
              </div>
              <div className="space-y-1.5">
                <span className="text-[10px] text-brand-textMuted block font-bold uppercase tracking-wider font-mono">Status State</span>
                <div className="w-full h-10 px-3 bg-brand-background/20 border border-brand-border rounded-xl flex items-center gap-2 opacity-70 select-none">
                  <span className="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse" /> Active Enterprise User
                </div>
              </div>
            </div>
          </Card>

          {/* Session Token Inspector */}
          <Card className="p-6" glow>
            <h2 className="text-xs font-bold text-white mb-3 uppercase tracking-wider flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Key className="w-4 h-4 text-brand-accent" /> JWT Access Token Inspector
              </span>
              <button
                onClick={() => setShowToken(!showToken)}
                className="text-[10px] text-brand-primary hover:text-brand-accent flex items-center gap-1.5 focus:outline-none cursor-pointer font-bold font-mono"
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
            <p className="text-[10px] text-brand-textSecondary mb-4 leading-relaxed font-mono">
              This signature token is appended automatically inside the headers of Axios network requests.
            </p>
            <div className="p-4 rounded-xl bg-brand-background/60 border border-brand-border/60">
              <span className="font-mono text-xs break-all block text-brand-accent/90 select-text">
                {showToken ? token : '••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••'}
              </span>
            </div>
          </Card>
        </div>

        {/* Configurations Column */}
        <Card className="p-6" glow>
          <h2 className="text-xs font-bold text-white mb-6 uppercase tracking-wider flex items-center gap-2">
            <Shield className="w-4 h-4 text-brand-accent" /> Security Parameters
          </h2>
          <div className="space-y-4 text-xs text-brand-textSecondary font-mono select-none">
            <div className="flex justify-between items-center py-2.5 border-b border-brand-border/40">
              <span>Token Expiration</span>
              <span className="font-bold text-white">60 Minutes</span>
            </div>
            <div className="flex justify-between items-center py-2.5 border-b border-brand-border/40">
              <span>Hashing Mechanism</span>
              <span className="font-bold text-white">bcrypt</span>
            </div>
            <div className="flex justify-between items-center py-2.5 border-b border-brand-border/40">
              <span>Signature Crypt</span>
              <span className="font-bold text-white">HS256</span>
            </div>
            <div className="flex justify-between items-center py-2.5">
              <span>Cors Allowed Origins</span>
              <Badge variant="secondary">All (*)</Badge>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
export type email = string;
