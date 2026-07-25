import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Activity, Shield, Cpu, Database, Server, RefreshCw, Layers, Terminal, Play, Circle } from 'lucide-react';
import { Card, Button, Badge } from '../components/ui/Primitives';

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

interface EventLog {
  id: string;
  time: string;
  type: 'INDEXED' | 'EMBEDDING' | 'WORKER' | 'RETRIEVER' | 'EVALUATION' | 'AGENT' | 'CACHE';
  message: string;
}

const INITIAL_LOGS: EventLog[] = [
  { id: '1', time: '20:41:02', type: 'CACHE', message: 'Query response index cache warmed in memory broker.' },
  { id: '2', time: '20:41:05', type: 'WORKER', message: 'Celery worker daemon indexer initialized successfully.' },
  { id: '3', time: '20:41:10', type: 'RETRIEVER', message: 'ChromaDB index mapping optimized (Cosine Similarity).' },
  { id: '4', time: '20:41:12', type: 'INDEXED', message: 'Document "Security_Manual_v2.pdf" indexed successfully (64 chunks).' },
  { id: '5', time: '20:41:15', type: 'EMBEDDING', message: 'SentenceTransformers vector weights mapped to cluster Security.' },
  { id: '6', time: '20:41:20', type: 'EVALUATION', message: 'Automatic evaluation run finished. Groundedness precision: 98%.' },
  { id: '7', time: '20:41:22', type: 'AGENT', message: 'Agentic session established with container ID: workspace_default_core.' }
];

const LOG_MESSAGES = [
  { type: 'EMBEDDING' as const, message: 'SentenceTransformers model encoded new semantic string vectors.' },
  { type: 'INDEXED' as const, message: 'ChromaDB collection mapping updated. Total index count increased.' },
  { type: 'WORKER' as const, message: 'Celery pipeline completed chunking task successfully.' },
  { type: 'RETRIEVER' as const, message: 'Retriever weights optimized. Index query latency down to 24ms.' },
  { type: 'CACHE' as const, message: 'Redis cache keys warmed. Session store initialized.' },
  { type: 'AGENT' as const, message: 'Retrieval-Augmented reasoning loops verified by evaluator.' }
];

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [logs, setLogs] = useState<EventLog[]>(INITIAL_LOGS);

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

  // Simulate active live event streaming log feed
  useEffect(() => {
    const interval = setInterval(() => {
      const randomMsg = LOG_MESSAGES[Math.floor(Math.random() * LOG_MESSAGES.length)];
      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
      
      const newLog: EventLog = {
        id: Date.now().toString(),
        time: timeStr,
        type: randomMsg.type,
        message: randomMsg.message
      };

      setLogs(prev => [newLog, ...prev.slice(0, 14)]);
    }, 4500);

    return () => clearInterval(interval);
  }, []);

  const getLogBadgeColor = (type: EventLog['type']) => {
    switch (type) {
      case 'INDEXED': return 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5';
      case 'EMBEDDING': return 'border-green-400/30 text-green-300 bg-green-400/5';
      case 'WORKER': return 'border-yellow-500/30 text-yellow-400 bg-yellow-500/5';
      case 'RETRIEVER': return 'border-brand-primary/30 text-brand-primary bg-brand-primary/5';
      case 'EVALUATION': return 'border-brand-accent/30 text-brand-accent bg-brand-accent/5';
      case 'AGENT': return 'border-white/30 text-white bg-white/5';
      case 'CACHE': return 'border-gray-500/30 text-gray-400 bg-gray-500/5';
      default: return 'border-brand-border text-brand-textMuted';
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto select-none relative z-10 font-sans">
      {/* Welcome Banner */}
      <Card className="flex items-center justify-between relative overflow-hidden border border-brand-primary/20 bg-gradient-to-r from-brand-surface/80 to-black/40 p-8 rounded-2xl" glow>
        <div className="space-y-1.5 relative z-10">
          <Badge variant="primary" className="mb-2">AegisAI OS Ready</Badge>
          <h1 className="text-3xl font-extrabold tracking-tight text-white uppercase tracking-wider">
            Mission Control: <span className="bg-gradient-to-r from-white via-brand-accent to-brand-primary bg-clip-text text-transparent">@{user?.username}</span>
          </h1>
          <p className="text-brand-textSecondary text-xs max-w-xl leading-relaxed font-mono">
            Operating system container active. Monitoring live vectors, background celery task loops, and grounding evaluator checks.
          </p>
        </div>
        <div className="w-14 h-14 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary shrink-0 relative z-10 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
          <Shield className="w-6 h-6 animate-pulse" />
        </div>
      </Card>

      {/* Mission Control Panel: Live Events & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Real-time System Status Nodes */}
        <Card className="lg:col-span-1 p-6 space-y-6" glow>
          <div className="flex justify-between items-center border-b border-brand-border/40 pb-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-primary" /> Active Nodes
            </h3>
            <button 
              onClick={fetchHealth} 
              disabled={refreshing}
              className="text-[10px] text-brand-primary hover:text-brand-accent font-mono flex items-center gap-1.5 cursor-pointer uppercase font-bold"
            >
              <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} /> Sync Nodes
            </button>
          </div>

          <div className="space-y-4 font-mono text-xs">
            {/* Database Node */}
            <div className="p-3.5 bg-brand-background/40 border border-brand-border/40 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-brand-primary" />
                <div>
                  <span className="text-white font-bold block text-[10px]">RELATIONAL_DB</span>
                  <span className="text-[8px] text-brand-textMuted">PostgreSQL Core</span>
                </div>
              </div>
              <Badge variant={health?.details?.database === 'ok' ? 'success' : 'warning'} className="text-[8px] tracking-wider py-0.5">
                {health?.details?.database === 'ok' ? 'ACTIVE' : 'OFFLINE'}
              </Badge>
            </div>

            {/* Redis Node */}
            <div className="p-3.5 bg-brand-background/40 border border-brand-border/40 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Server className="w-4 h-4 text-brand-accent" />
                <div>
                  <span className="text-white font-bold block text-[10px]">CACHE_BROKER</span>
                  <span className="text-[8px] text-brand-textMuted">Redis Task Queue</span>
                </div>
              </div>
              <Badge variant={health?.details?.redis === 'ok' ? 'success' : 'warning'} className="text-[8px] tracking-wider py-0.5">
                {health?.details?.redis === 'ok' ? 'ACTIVE' : 'OFFLINE'}
              </Badge>
            </div>

            {/* ChromaDB Node */}
            <div className="p-3.5 bg-brand-background/40 border border-brand-border/40 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Layers className="w-4 h-4 text-brand-accent" />
                <div>
                  <span className="text-white font-bold block text-[10px]">VECTOR_STORE</span>
                  <span className="text-[8px] text-brand-textMuted">ChromaDB Collection</span>
                </div>
              </div>
              <Badge variant={health?.details?.chromadb === 'ok' ? 'success' : 'warning'} className="text-[8px] tracking-wider py-0.5">
                {health?.details?.chromadb === 'ok' ? 'ACTIVE' : 'OFFLINE'}
              </Badge>
            </div>

            {/* Celery Node */}
            <div className="p-3.5 bg-brand-background/40 border border-brand-border/40 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Cpu className="w-4 h-4 text-brand-primary" />
                <div>
                  <span className="text-white font-bold block text-[10px]">DAEMON_WORKER</span>
                  <span className="text-[8px] text-brand-textMuted">Celery Indexing Loop</span>
                </div>
              </div>
              <Badge variant={health?.details?.background_workers === 'ok' ? 'success' : 'warning'} className="text-[8px] tracking-wider py-0.5">
                {health?.details?.background_workers === 'ok' ? 'ACTIVE' : 'OFFLINE'}
              </Badge>
            </div>
          </div>
        </Card>

        {/* Live Event Stream Logs */}
        <Card className="lg:col-span-2 p-6 space-y-4" glow>
          <div className="flex justify-between items-center border-b border-brand-border/40 pb-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Terminal className="w-4 h-4 text-brand-primary" /> Event Stream Matrix
            </h3>
            <span className="text-[9px] text-brand-primary font-mono flex items-center gap-1">
              <Circle className="w-2 h-2 fill-brand-primary animate-pulse" /> LIVE STREAMING
            </span>
          </div>

          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1 select-text font-mono text-[10px]">
            {logs.map((log) => (
              <div 
                key={log.id} 
                className="flex items-start gap-3 p-3.5 bg-brand-background/25 border border-brand-border/30 rounded-xl hover:border-brand-primary/20 transition-all duration-200"
              >
                <span className="text-brand-textMuted font-mono shrink-0 select-none">[{log.time}]</span>
                <span className={`px-2 py-0.5 border rounded text-[8px] font-bold shrink-0 ${getLogBadgeColor(log.type)}`}>
                  {log.type}
                </span>
                <span className="text-gray-300 leading-relaxed break-all select-text">{log.message}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Engine Specs */}
      <Card glow className="p-6">
        <h2 className="text-xs font-bold text-white mb-4 tracking-wider uppercase border-b border-brand-border/30 pb-2 flex items-center gap-2 font-mono">
          <Terminal className="w-4 h-4 text-brand-primary" /> OS Kernel Specifications
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-brand-background/40 border border-brand-border/40 hover:border-brand-border/80 transition-colors">
            <span className="block font-bold text-white mb-1.5 uppercase tracking-wider text-[9px] text-brand-textMuted">Core Kernel</span>
            <span className="text-brand-text">FastAPI v0.110 (Python 3.12)</span>
          </div>
          <div className="p-4 rounded-xl bg-brand-background/40 border border-brand-border/40 hover:border-brand-border/80 transition-colors">
            <span className="block font-bold text-white mb-1.5 uppercase tracking-wider text-[9px] text-brand-textMuted">Logger Stream</span>
            <span className="text-brand-text">Structlog JSON Format</span>
          </div>
          <div className="p-4 rounded-xl bg-brand-background/40 border border-brand-border/40 hover:border-brand-border/80 transition-colors">
            <span className="block font-bold text-white mb-1.5 uppercase tracking-wider text-[9px] text-brand-textMuted">RAG Engine</span>
            <span className="text-brand-text">SentenceTransformers Embeddings</span>
          </div>
          <div className="p-4 rounded-xl bg-brand-background/40 border border-brand-border/40 hover:border-brand-border/80 transition-colors">
            <span className="block font-bold text-white mb-1.5 uppercase tracking-wider text-[9px] text-brand-textMuted">Execution Engine</span>
            <span className="text-brand-text">Celery Async Task Workers</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default DashboardPage;
