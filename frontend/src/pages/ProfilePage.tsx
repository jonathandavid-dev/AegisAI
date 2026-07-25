import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { User, Shield, Mail, Key, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { Card, Button, Input, Avatar, Badge } from '../components/ui/Primitives';

export const ProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);

    try {
      const payload: any = {};
      if (fullName !== user?.full_name) payload.full_name = fullName;
      if (email !== user?.email) payload.email = email;
      if (password) payload.password = password;

      if (Object.keys(payload).length === 0) {
        setSuccess("No changes made.");
        setSubmitting(false);
        return;
      }

      await api.patch('/auth/profile', payload);
      setSuccess("Profile updated successfully!");
      setPassword('');
      await refreshUser();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Profile update failed. Verify password meets complexity constraints.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">Account Profile</h1>
          <p className="text-xs text-brand-textSecondary mt-1">Manage user information, corporate credentials, and secure permissions</p>
        </div>
        <Badge variant="primary" className="flex items-center gap-1.5 py-1 px-3">
          <Shield className="w-3.5 h-3.5" /> {user?.role || 'VIEWER'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <Card className="flex flex-col items-center p-6 text-center space-y-4" glow>
          <Avatar name={user?.username || 'US'} size="lg" className="w-20 h-20 text-3xl font-extrabold" />
          <div>
            <h2 className="text-lg font-bold text-white">{user?.full_name || user?.username}</h2>
            <p className="text-brand-textMuted text-xs font-mono mt-0.5">@{user?.username}</p>
          </div>

          <div className="w-full border-t border-brand-border/40 pt-4 space-y-2.5 text-left text-xs font-mono text-brand-textSecondary select-none">
            <div className="flex justify-between">
              <span>Account Type</span>
              <span className="text-white font-bold">{user?.role}</span>
            </div>
            <div className="flex justify-between">
              <span>Verified Status</span>
              <span className={user?.is_verified ? "text-green-400 font-bold" : "text-brand-textMuted font-bold"}>
                {user?.is_verified ? "VERIFIED" : "UNVERIFIED"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Member Since</span>
              <span className="text-white font-bold">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </Card>

        {/* Edit Form */}
        <Card className="md:col-span-2 p-6" glow>
          <h3 className="text-xs font-bold uppercase tracking-wider text-white mb-6">Modify Credentials</h3>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-950/20 border border-red-800/30 text-red-400 text-xs flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 rounded-xl bg-green-950/20 border border-green-800/30 text-green-400 text-xs flex items-start gap-3">
              <CheckCircle className="w-5 h-5 shrink-0 text-green-400" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <User className="w-3.5 h-3.5 text-brand-primary" /> Full Name
                </label>
                <Input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Smith"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <Mail className="w-3.5 h-3.5 text-brand-primary" /> Corporate Email
                </label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jsmith@corporate.com"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Key className="w-3.5 h-3.5 text-brand-primary" /> Change Password
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Leave blank to keep current password"
              />
              <span className="text-[9px] text-brand-textMuted block font-sans select-none">
                Must contain at least 8 characters, one number, one uppercase, and one special character.
              </span>
            </div>

            <div className="flex justify-end pt-4 border-t border-brand-border/40">
              <Button
                type="submit"
                disabled={submitting}
                className="text-xs font-bold"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Saving...
                  </>
                ) : (
                  "Save Profile Changes"
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
