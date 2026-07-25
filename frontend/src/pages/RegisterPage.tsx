import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield, Key, User, Mail, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, Button, Input } from '../components/ui/Primitives';
import { CinematicBackdrop } from '../components/ui/CinematicBackdrop';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(username, email, password);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2500);
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        'Onboarding failed. Verify email is unique and password satisfies constraints.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-background flex items-center justify-center px-4 relative overflow-hidden">
      <CinematicBackdrop />

      <Card className="w-full max-w-md border-brand-border shadow-2xl relative z-10 p-8" glow>
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-brand-primary/15 border border-brand-primary/30 flex items-center justify-center text-brand-primary mb-4 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
            <Shield className="w-6 h-6 animate-pulse" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white uppercase tracking-wider">Register Account</h1>
          <p className="text-[#9CA3AF] text-xs mt-1">Create your enterprise account on AegisAI</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/20 border border-red-800/30 text-red-400 text-xs flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 rounded-xl bg-green-950/20 border border-green-800/30 text-green-400 text-xs flex items-start gap-3">
            <CheckCircle className="w-5 h-5 shrink-0 text-green-400 animate-pulse" />
            <span>Registration successful! Redirecting to login portal...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <User className="w-3.5 h-3.5 text-brand-primary" /> Username
            </label>
            <Input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. jsmith"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Mail className="w-3.5 h-3.5 text-brand-primary" /> Corporate Email
            </label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jsmith@corporate.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Key className="w-3.5 h-3.5 text-brand-primary" /> Password
            </label>
            <Input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
            />
          </div>

          <Button
            type="submit"
            disabled={submitting || success}
            className="w-full font-bold mt-4"
          >
            {submitting ? 'Generating Account...' : 'Create Account'}
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-brand-textSecondary border-t border-brand-border/40 pt-4">
          Already registered?{' '}
          <Link to="/login" className="text-brand-primary hover:text-brand-accent transition-colors font-semibold">
            Sign In
          </Link>
        </div>
      </Card>
    </div>
  );
};
export type password = string;
