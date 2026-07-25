import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield, Key, User, AlertCircle } from 'lucide-react';
import { Card, Button, Input } from '../components/ui/Primitives';
import { CinematicBackdrop } from '../components/ui/CinematicBackdrop';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({ username_or_email: username, password });
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(
        err.response?.data?.message || 
        'Authorization failed. Please check credentials.'
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
          <h1 className="text-2xl font-extrabold tracking-tight text-white uppercase tracking-wider">Access Gateway</h1>
          <p className="text-[#9CA3AF] text-xs mt-1">Authenticate to access AegisAI Knowledge Platform</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-950/20 border border-red-800/30 text-red-400 text-xs flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <User className="w-3.5 h-3.5 text-brand-primary" /> Username
            </label>
            <Input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. administrator"
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
              placeholder="••••••••"
            />
          </div>

          <Button
            type="submit"
            disabled={submitting}
            className="w-full font-bold mt-2"
          >
            {submitting ? 'Authenticating Credentials...' : 'Sign In'}
          </Button>
        </form>

        <div className="mt-8 text-center text-xs text-brand-textSecondary border-t border-brand-border/40 pt-6">
          Need an account?{' '}
          <Link to="/register" className="text-brand-primary hover:text-brand-accent transition-colors font-semibold">
            Register Account
          </Link>
        </div>
      </Card>
    </div>
  );
};
