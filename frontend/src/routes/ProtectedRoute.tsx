import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield } from 'lucide-react';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-background flex flex-col items-center justify-center gap-4">
        <Shield className="w-12 h-12 text-brand-primary animate-spin" />
        <span className="text-sm font-mono tracking-widest text-brand-primary">
          HYDRATING AEGIS SECURE CONTEXT...
        </span>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
