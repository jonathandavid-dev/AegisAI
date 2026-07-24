import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Activity, Shield, Cpu, Database, Server, RefreshCw } from 'lucide-react';

interface HealthStatus {
  status: string;
  details: {
    database: string;
    redis: string;
    chromadb: string;
    llm_provider: string;
    background_workers: string;
  };
}

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    setRefreshing(true);
    try {
      const response = await api.get<HealthStatus>('/health/ready');
      setHealth(response.data);
    } catch (error: any) {
      console.error("Health check lookup failed", error);
      if (error.response?.data) {
        setHealth(error.response.data);
      } else {
        setHealth(null);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="glass-card flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Welcome Back, {user?.username}</h1>
          <p className="text-gray-400 text-sm">Monitor platform status, upload knowledge vectors, and query the cognitive layer.</p>
        </div>
        <div className="w-16 h-16 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary hidden sm:flex">
          <Shield className="w-8 h-8" />
        </div>
      </div>

      {/* Systems Status Header */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold tracking-wide uppercase text-gray-400 flex items-center gap-2">
            <Activity className="w-5 h-5 text-brand-primary" /> Backing Infrastructure Health
          </h2>
          <button 
            onClick={fetchHealth} 
            disabled={refreshing}
            className="flex items-center gap-1.5 text-xs text-brand-primary hover:text-brand-accent transition-colors focus:outline-none"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} /> Refresh Status
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 rounded-xl bg-brand-surface/40 animate-pulse border border-brand-border/40" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Database Card */}
            <div className="glass-card relative overflow-hidden">
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-semibold text-gray-400">PostgreSQL Database</span>
                <Database className="w-5 h-5 text-brand-primary" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white uppercase">{health?.details?.database === 'ok' ? 'online' : 'offline'}</span>
                <span className={`w-2 h-2 rounded-full ${health?.details?.database === 'ok' ? 'bg-green-400 animate-ping' : 'bg-red-400'}`} />
              </div>
              <p className="text-xs text-gray-400 mt-2">Relational database core (SQLAlchemy 2.0 ORM)</p>
            </div>

            {/* Redis Card */}
            <div className="glass-card relative overflow-hidden">
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-semibold text-gray-400">Redis Broker</span>
                <Server className="w-5 h-5 text-brand-accent" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white uppercase">{health?.details?.redis === 'ok' ? 'online' : 'offline'}</span>
                <span className={`w-2 h-2 rounded-full ${health?.details?.redis === 'ok' ? 'bg-green-400 animate-ping' : 'bg-red-400'}`} />
              </div>
              <p className="text-xs text-gray-400 mt-2">Caching & background task transmission channel</p>
            </div>

            {/* Celery Task Worker Card */}
            <div className="glass-card relative overflow-hidden">
              <div className="flex justify-between items-start mb-4">
                <span className="text-sm font-semibold text-gray-400">Celery Worker Node</span>
                <Cpu className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white uppercase">{health?.details?.background_workers === 'ok' ? 'online' : 'offline'}</span>
                <span className={`w-2 h-2 rounded-full ${health?.details?.background_workers === 'ok' ? 'bg-green-400 animate-ping' : 'bg-red-400'}`} />
              </div>
              <p className="text-xs text-gray-400 mt-2">Asynchronous pipeline parsing nodes</p>
            </div>
          </div>
        )}
      </div>

      {/* Platform Overview */}
      <div className="glass-card">
        <h2 className="text-lg font-bold text-white mb-4">AegisAI Architecture Specs</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-sm text-gray-400">
          <div className="p-4 rounded-lg bg-brand-background/40 border border-brand-border/40">
            <span className="block font-medium text-white mb-1">Backend Framework</span>
            FastAPI v0.110 (Python 3.12)
          </div>
          <div className="p-4 rounded-lg bg-brand-background/40 border border-brand-border/40">
            <span className="block font-medium text-white mb-1">Structured Logger</span>
            Structlog (JSON Stream Format)
          </div>
          <div className="p-4 rounded-lg bg-brand-background/40 border border-brand-border/40">
            <span className="block font-medium text-white mb-1">Database ORM</span>
            SQLAlchemy 2.0 (Async Engine)
          </div>
          <div className="p-4 rounded-lg bg-brand-background/40 border border-brand-border/40">
            <span className="block font-medium text-white mb-1">Frontend Bundler</span>
            Vite + React 18 + TS
          </div>
        </div>
      </div>
    </div>
  );
};
