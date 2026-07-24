import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import { User, Shield, Mail, Key, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

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
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between border-b border-brand-border/60 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Account Profile</h1>
          <p className="text-gray-400 text-xs mt-1">Manage user information, corporate credentials, and secure permissions</p>
        </div>
        <div className="flex items-center gap-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-lg px-2.5 py-1 text-brand-primary text-xs font-mono uppercase tracking-wider">
          <Shield className="w-3.5 h-3.5" /> {user?.role || 'VIEWER'}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="glass-card flex flex-col items-center p-6 text-center space-y-4">
          <div className="w-20 h-20 rounded-full bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary text-3xl font-bold uppercase shadow-inner">
            {user?.username.slice(0, 2) || 'US'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{user?.full_name || user?.username}</h2>
            <p className="text-gray-400 text-xs font-mono">@{user?.username}</p>
          </div>

          <div className="w-full border-t border-brand-border/40 pt-4 space-y-2 text-left text-xs font-mono text-gray-400">
            <div className="flex justify-between">
              <span>Account Type</span>
              <span className="text-white font-semibold">{user?.role}</span>
            </div>
            <div className="flex justify-between">
              <span>Verified Status</span>
              <span className={user?.is_verified ? "text-green-400 font-semibold" : "text-gray-500 font-semibold"}>
                {user?.is_verified ? "VERIFIED" : "UNVERIFIED"}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Member Since</span>
              <span className="text-white font-semibold">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Edit Form */}
        <div className="glass-card md:col-span-2 p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-6">Modify Credentials</h3>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-950/40 border border-red-800/40 text-red-300 text-xs flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 rounded-xl bg-green-950/40 border border-green-800/40 text-green-300 text-xs flex items-start gap-3">
              <CheckCircle className="w-5 h-5 shrink-0 text-green-400" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" /> Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full glass-input"
                  placeholder="John Smith"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5" /> Corporate Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full glass-input"
                  placeholder="jsmith@corporate.com"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> Change Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full glass-input"
                placeholder="Leave blank to keep current password"
              />
              <span className="text-[10px] text-gray-500 block">
                Must contain at least 8 characters, one number, one uppercase, and one special character.
              </span>
            </div>

            <div className="flex justify-end pt-4 border-t border-brand-border/40">
              <button
                type="submit"
                disabled={submitting}
                className="btn-primary font-semibold flex items-center gap-2 text-xs"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Saving...
                  </>
                ) : (
                  "Save Profile Changes"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
