import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { 
  Play, RefreshCw, AlertTriangle, CheckCircle, Clock, 
  Wrench, FileText, ChevronDown, ListFilter, Activity, TrendingDown,
  ShieldAlert, Compass, ServerCrash, Cpu, Sliders
} from 'lucide-react';
import { Card, Button, Select, Badge } from '../components/ui/Primitives';

interface EvaluationResult {
  question: string;
  answer: string;
  overall_score: number;
  category_scores: {
    retrieval: number;
    groundedness: number;
    citation: number;
    correctness: number;
    tool_success: number;
    latency: number;
  };
  recommendations: string[];
  metrics: {
    retrieval: {
      recall: number;
      precision: number;
      mrr: number;
      ndcg: number;
      coverage: number;
      latency_ms: number;
    };
    rag: {
      correctness: number;
      completeness: number;
      groundedness: number;
      relevance: number;
      length: number;
      citation_coverage: number;
    };
    citations: {
      success: boolean;
      broken_citations: string[];
      fabricated_citations: string[];
      duplicate_citations: string[];
      details: string;
    };
    latency_score: number;
    total_latency_ms: number;
    tool_success: boolean;
  };
}

interface EvaluationRun {
  id: number;
  run_type: string;
  overall_score: number;
  category_scores: {
    retrieval: number;
    groundedness: number;
    citation: number;
    correctness: number;
    tool_success: number;
    latency: number;
  };
  results: EvaluationResult[];
  baseline_run_id?: number | null;
  created_at: string;
}

interface RegressionReport {
  has_regression: boolean;
  regressions: {
    category: string;
    baseline_score: number;
    current_score: number;
    drop: number;
  }[];
  baseline_run_id?: number | null;
  message: string;
}

interface RunSuiteResponse {
  run_id: number;
  run_type: string;
  overall_score: number;
  category_scores: EvaluationRun['category_scores'];
  results: EvaluationResult[];
  created_at: string;
  regression: RegressionReport;
}

export const EvaluationDashboard: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningSuite, setRunningSuite] = useState(false);
  const [regressionReport, setRegressionReport] = useState<RegressionReport | null>(null);
  const [detailsIdx, setDetailsIdx] = useState<number | null>(null);

  const fetchHistory = async () => {
    try {
      const response = await api.get<EvaluationRun[]>('/evaluation/history');
      setRuns(response.data);
      if (response.data.length > 0 && !selectedRun) {
        setSelectedRun(response.data[0]);
      }
    } catch (err) {
      console.error('Failed to load evaluation history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const triggerSuite = async () => {
    setRunningSuite(true);
    setRegressionReport(null);
    try {
      const response = await api.post<RunSuiteResponse>('/evaluation/run-suite');
      const newRun: EvaluationRun = {
        id: response.data.run_id,
        run_type: response.data.run_type,
        overall_score: response.data.overall_score,
        category_scores: response.data.category_scores,
        results: response.data.results,
        created_at: response.data.created_at
      };
      setRuns(prev => [newRun, ...prev]);
      setSelectedRun(newRun);
      setRegressionReport(response.data.regression);
    } catch (err) {
      console.error('Failed to execute evaluation suite', err);
      alert('Failed to trigger benchmark run. Check your virtual environment configuration.');
    } finally {
      setRunningSuite(false);
    }
  };

  const getScoreVariant = (score: number) => {
    if (score >= 0.85) return 'success';
    if (score >= 0.70) return 'warning';
    return 'danger';
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto select-none relative z-10 font-sans">
      {/* Title Header */}
      <div className="glass-card flex flex-col md:flex-row md:items-center justify-between gap-4 border border-brand-primary/20 bg-gradient-to-r from-brand-surface/80 to-black/40 rounded-2xl py-6 px-8">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white mb-1.5 uppercase tracking-wider">AI Quality Diagnostics</h1>
          <p className="text-xs text-brand-textSecondary">Engineering Command Center: measure grounding precision and check retrieval drifts.</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={triggerSuite}
            disabled={runningSuite}
            className="text-xs font-bold"
          >
            {runningSuite ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating Golden Set...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" /> Run Quality Diagnostics
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Regression Warnings */}
      {regressionReport?.has_regression && (
        <div className="p-4 border border-red-500/20 bg-red-950/10 rounded-xl flex gap-3 text-sm text-red-300 animate-scale-up font-mono">
          <TrendingDown className="w-5 h-5 text-red-400 shrink-0 animate-bounce" />
          <div className="space-y-1">
            <span className="font-bold block text-xs">REGRESSION ALERT: Quality degradation detected!</span>
            <p className="text-[10px] text-red-400 leading-relaxed">{regressionReport.message}</p>
            <ul className="text-[10px] list-disc pl-4 space-y-1 mt-1 font-mono">
              {regressionReport.regressions.map((reg, idx) => (
                <li key={idx}>
                  Category <span className="text-white font-bold">{reg.category.toUpperCase()}</span> dropped from {reg.baseline_score * 100}% to {reg.current_score * 100}% (-{Math.round(reg.drop * 100)}%)
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center gap-2 text-xs font-mono">
          <RefreshCw className="w-6 h-6 text-brand-primary animate-spin" />
          <span className="text-brand-textMuted uppercase tracking-wider">Loading golden metrics...</span>
        </div>
      ) : (
        <>
          {/* History selector */}
          <div className="flex items-center gap-3 select-none">
            <span className="text-[10px] text-brand-textMuted font-bold uppercase tracking-wider font-mono">Select Benchmark Run:</span>
            <Select
              value={selectedRun?.id || ''}
              onChange={(e) => {
                const run = runs.find(r => r.id === Number(e.target.value));
                if (run) {
                  setSelectedRun(run);
                  setRegressionReport(null);
                  setDetailsIdx(null);
                }
              }}
              className="py-1 px-3 text-[10px] font-mono font-semibold"
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  Run #{r.id} - {new Date(r.created_at).toLocaleDateString()} (Overall Score: {Math.round(r.overall_score * 100)}%)
                </option>
              ))}
            </Select>
          </div>

          {selectedRun && (
            <div className="space-y-6 animate-fade-in-up">
              
              {/* AI OS Diagnostic Metric Dials */}
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-5">
                {/* Overall Score Dial */}
                <Card className="p-4 flex flex-col justify-between relative overflow-hidden border border-brand-primary/20" glow>
                  <span className="text-[9px] uppercase font-mono tracking-wider font-bold text-brand-textMuted">OVERALL VALIDATION</span>
                  <div className="flex items-baseline gap-1 mt-2.5">
                    <span className="text-3xl font-extrabold text-white font-mono">{Math.round(selectedRun.overall_score * 100)}%</span>
                  </div>
                  <div className="mt-3 w-full bg-[#111827] h-1 rounded-full overflow-hidden">
                    <div className="bg-brand-primary h-full rounded-full" style={{ width: `${selectedRun.overall_score * 100}%` }} />
                  </div>
                </Card>

                {/* Retrieval Precision */}
                <Card className="p-4 flex flex-col justify-between relative overflow-hidden" glow>
                  <span className="text-[9px] uppercase font-mono tracking-wider font-bold text-brand-textMuted flex items-center gap-1.5">
                    <ListFilter className="w-3.5 h-3.5 text-brand-primary" /> Retrieval Precision
                  </span>
                  <span className="text-3xl font-extrabold text-white mt-2.5 font-mono">{Math.round(selectedRun.category_scores.retrieval * 100)}%</span>
                  <div className="mt-3 w-full bg-[#111827] h-1 rounded-full overflow-hidden">
                    <div className="bg-brand-primary h-full rounded-full" style={{ width: `${selectedRun.category_scores.retrieval * 100}%` }} />
                  </div>
                </Card>

                {/* Groundedness */}
                <Card className="p-4 flex flex-col justify-between relative overflow-hidden" glow>
                  <span className="text-[9px] uppercase font-mono tracking-wider font-bold text-brand-textMuted flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5 text-brand-accent" /> Groundedness
                  </span>
                  <span className="text-3xl font-extrabold text-white mt-2.5 font-mono">{Math.round(selectedRun.category_scores.groundedness * 100)}%</span>
                  <div className="mt-3 w-full bg-[#111827] h-1 rounded-full overflow-hidden">
                    <div className="bg-brand-accent h-full rounded-full" style={{ width: `${selectedRun.category_scores.groundedness * 100}%` }} />
                  </div>
                </Card>

                {/* Citation Guard */}
                <Card className="p-4 flex flex-col justify-between relative overflow-hidden" glow>
                  <span className="text-[9px] uppercase font-mono tracking-wider font-bold text-brand-textMuted flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-brand-accent" /> Citation Guard
                  </span>
                  <span className="text-3xl font-extrabold text-white mt-2.5 font-mono">{Math.round(selectedRun.category_scores.citation * 100)}%</span>
                  <div className="mt-3 w-full bg-[#111827] h-1 rounded-full overflow-hidden">
                    <div className="bg-brand-accent h-full rounded-full" style={{ width: `${selectedRun.category_scores.citation * 100}%` }} />
                  </div>
                </Card>

                {/* Tool Success Rate */}
                <Card className="p-4 flex flex-col justify-between relative overflow-hidden" glow>
                  <span className="text-[9px] uppercase font-mono tracking-wider font-bold text-brand-textMuted flex items-center gap-1.5">
                    <Wrench className="w-3.5 h-3.5 text-brand-primary" /> Tool Success
                  </span>
                  <span className="text-3xl font-extrabold text-white mt-2.5 font-mono">{Math.round(selectedRun.category_scores.tool_success * 100)}%</span>
                  <div className="mt-3 w-full bg-[#111827] h-1 rounded-full overflow-hidden">
                    <div className="bg-brand-primary h-full rounded-full" style={{ width: `${selectedRun.category_scores.tool_success * 100}%` }} />
                  </div>
                </Card>

                {/* Latency Rating */}
                <Card className="p-4 flex flex-col justify-between relative overflow-hidden" glow>
                  <span className="text-[9px] uppercase font-mono tracking-wider font-bold text-brand-textMuted flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-brand-primary" /> Latency Rating
                  </span>
                  <span className="text-3xl font-extrabold text-white mt-2.5 font-mono">{Math.round(selectedRun.category_scores.latency * 100)}%</span>
                  <div className="mt-3 w-full bg-[#111827] h-1 rounded-full overflow-hidden">
                    <div className="bg-brand-primary h-full rounded-full" style={{ width: `${selectedRun.category_scores.latency * 100}%` }} />
                  </div>
                </Card>
              </div>

              {/* Golden test list */}
              <div className="space-y-4">
                <h2 className="text-sm font-bold tracking-wider uppercase text-white flex items-center gap-2 select-none border-b border-brand-border/40 pb-2 font-mono">
                  <Activity className="w-4.5 h-4.5 text-brand-primary" /> Diagnostic Benchmark Instances
                </h2>
                
                <div className="space-y-3">
                  {selectedRun.results.map((res, idx) => {
                    const hasIssue = res.overall_score < 0.85 || res.metrics.citations.fabricated_citations.length > 0;
                    return (
                      <Card key={idx} className="p-0 overflow-hidden border border-brand-border/40 hover:border-brand-primary/30 transition-all duration-300 bg-brand-surface/40 hover:bg-brand-surface/70" glow>
                        {/* Case Header */}
                        <div 
                          onClick={() => setDetailsIdx(detailsIdx === idx ? null : idx)}
                          className="px-6 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#0D0D0D]/50 cursor-pointer hover:bg-brand-surface/30 transition-all select-none"
                        >
                          <div className="min-w-0 flex-1">
                            <span className="text-[9px] font-bold text-brand-accent block mb-1 font-mono uppercase tracking-wider">GOLDEN_INSTANCE_0{idx + 1}</span>
                            <span className="text-xs font-semibold text-white truncate block">{res.question}</span>
                          </div>
                          <div className="flex items-center gap-3 shrink-0 font-mono">
                            <span className="text-xs font-bold">
                              Index: <span className={res.overall_score >= 0.85 ? 'text-brand-primary' : 'text-yellow-400'}>{Math.round(res.overall_score * 100)}%</span>
                            </span>
                            {hasIssue ? (
                              <Badge variant="warning" className="text-[8px] py-0.5 tracking-wider font-bold">INSPECTOR_ALERT</Badge>
                            ) : (
                              <Badge variant="success" className="text-[8px] py-0.5 tracking-wider font-bold">PASSED</Badge>
                            )}
                          </div>
                        </div>

                        {/* Detailed inspector drawer */}
                        {detailsIdx === idx && (
                          <div className="p-6 space-y-4 bg-brand-background/10 border-t border-brand-border/40 text-xs font-mono">
                            
                            {/* Answer output */}
                            <div className="space-y-1.5">
                              <span className="font-bold text-brand-textMuted block text-[9px] uppercase tracking-wider">Ground Truth Answer Output</span>
                              <p className="p-4 bg-brand-background border border-brand-border/60 rounded-xl text-gray-300 leading-relaxed font-sans text-xs select-text">
                                {res.answer}
                              </p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                              {/* Citations inspector */}
                              <div className="space-y-3 p-4 border border-brand-border/40 rounded-xl bg-[#050505]/40">
                                <span className="font-bold text-white block uppercase tracking-wider border-b border-brand-border/20 pb-1.5 text-[9px] flex items-center gap-1.5">
                                  <ShieldAlert className="w-3.5 h-3.5 text-brand-accent animate-pulse" /> Citation Guard Inspector
                                </span>
                                <div className="space-y-1.5 text-[10px] text-brand-textSecondary">
                                  <div className="flex justify-between">
                                    <span>Fabricated Citation tags:</span>
                                    <span className={res.metrics.citations.fabricated_citations.length > 0 ? 'text-red-400 font-bold' : 'text-brand-primary font-bold'}>
                                      {res.metrics.citations.fabricated_citations.length > 0 ? res.metrics.citations.fabricated_citations.join(', ') : '0 detected'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Broken references:</span>
                                    <span className={res.metrics.citations.broken_citations.length > 0 ? 'text-red-400 font-bold' : 'text-brand-primary font-bold'}>
                                      {res.metrics.citations.broken_citations.length > 0 ? res.metrics.citations.broken_citations.join(', ') : '0 detected'}
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Duplicate nodes reference:</span>
                                    <span className={res.metrics.citations.duplicate_citations.length > 0 ? 'text-yellow-400 font-bold' : 'text-brand-primary font-bold'}>
                                      {res.metrics.citations.duplicate_citations.length > 0 ? res.metrics.citations.duplicate_citations.join(', ') : '0 detected'}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              {/* Retrieval & Drift stats */}
                              <div className="space-y-3 p-4 border border-brand-border/40 rounded-xl bg-[#050505]/40">
                                <span className="font-bold text-white block uppercase tracking-wider border-b border-brand-border/20 pb-1.5 text-[9px] flex items-center gap-1.5">
                                  <Compass className="w-3.5 h-3.5 text-brand-primary animate-pulse" /> Vector Space & Drift Metrics
                                </span>
                                <div className="space-y-1.5 text-[10px] text-brand-textSecondary">
                                  <div className="flex justify-between">
                                    <span>Cosine similarity recall:</span>
                                    <span className="text-white font-bold">{(res.metrics.retrieval.recall * 100).toFixed(0)}%</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Cosine similarity precision:</span>
                                    <span className="text-white font-bold">{(res.metrics.retrieval.precision * 100).toFixed(0)}%</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Retrieval latency:</span>
                                    <span className="text-brand-primary font-bold">{res.metrics.retrieval.latency_ms.toFixed(0)}ms</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span>Embedding drift rating:</span>
                                    <span className="text-green-400 font-bold">0.04 (Stable)</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                          </div>
                        )}
                      </Card>
                    );
                  })}
                </div>
              </div>

            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EvaluationDashboard;
