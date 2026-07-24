import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { 
  Play, RefreshCw, AlertTriangle, CheckCircle, Clock, 
  Wrench, FileText, ChevronDown, ListFilter, Activity, TrendingDown
} from 'lucide-react';

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

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return 'text-green-400 border-green-500/30 bg-green-500/10';
    if (score >= 0.70) return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
    return 'text-red-400 border-red-500/30 bg-red-500/10';
  };

  return (
    <div className="space-y-8">
      {/* Title block */}
      <div className="glass-card flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">AI Quality & Evaluation</h1>
          <p className="text-gray-400 text-sm">Validate groundedness, citations, hallucination rates, and performance across golden datasets.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={triggerSuite}
            disabled={runningSuite}
            className="px-4 py-2.5 bg-brand-primary text-white text-xs font-semibold uppercase tracking-wider rounded-xl hover:opacity-90 transition-opacity flex items-center gap-2 focus:outline-none disabled:opacity-50"
          >
            {runningSuite ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" /> Evaluating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" /> Trigger Benchmarks
              </>
            )}
          </button>
        </div>
      </div>

      {/* Regression alert block */}
      {regressionReport?.has_regression && (
        <div className="p-4 border border-red-500/30 bg-red-950/20 rounded-2xl flex gap-3 text-sm text-red-300">
          <TrendingDown className="w-5 h-5 text-red-400 shrink-0 animate-bounce" />
          <div className="space-y-1">
            <span className="font-bold block">Warning: Quality Regression Detected!</span>
            <p className="text-xs text-red-400">{regressionReport.message}</p>
            <ul className="text-xs list-disc pl-4 space-y-1 mt-1.5 font-mono">
              {regressionReport.regressions.map((reg, idx) => (
                <li key={idx}>
                  Category <span className="text-white font-semibold">{reg.category.toUpperCase()}</span> dropped from {reg.baseline_score * 100}% to {reg.current_score * 100}% (-{Math.round(reg.drop * 100)}%)
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 text-brand-primary animate-spin" />
        </div>
      ) : (
        <>
          {/* History selector */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider font-mono">Historical runs:</span>
            <div className="relative">
              <select
                value={selectedRun?.id || ''}
                onChange={(e) => {
                  const run = runs.find(r => r.id === Number(e.target.value));
                  if (run) {
                    setSelectedRun(run);
                    setRegressionReport(null);
                    setDetailsIdx(null);
                  }
                }}
                className="appearance-none bg-brand-surface border border-brand-border/60 text-white text-xs px-3.5 py-2 pr-8 rounded-lg focus:outline-none focus:border-brand-primary font-mono cursor-pointer"
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    Run #{r.id} - {new Date(r.created_at).toLocaleString()} (Score: {Math.round(r.overall_score * 100)}%)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-400 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {selectedRun && (
            <div className="space-y-8">
              {/* Quality Score Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(selectedRun.overall_score)}`}>
                  <span className="text-[10px] uppercase font-mono tracking-wider font-bold opacity-80">Overall QA Score</span>
                  <span className="text-3xl font-extrabold mt-1">{Math.round(selectedRun.overall_score * 100)}%</span>
                </div>
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(selectedRun.category_scores.retrieval)}`}>
                  <span className="text-[10px] uppercase font-mono tracking-wider font-bold opacity-80 flex items-center gap-1">
                    <FileText className="w-3.5 h-3.5" /> Retrieval
                  </span>
                  <span className="text-3xl font-extrabold mt-1">{Math.round(selectedRun.category_scores.retrieval * 100)}%</span>
                </div>
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(selectedRun.category_scores.groundedness)}`}>
                  <span className="text-[10px] uppercase font-mono tracking-wider font-bold opacity-80 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" /> Groundedness
                  </span>
                  <span className="text-3xl font-extrabold mt-1">{Math.round(selectedRun.category_scores.groundedness * 100)}%</span>
                </div>
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(selectedRun.category_scores.citation)}`}>
                  <span className="text-[10px] uppercase font-mono tracking-wider font-bold opacity-80 flex items-center gap-1">
                    <ListFilter className="w-3.5 h-3.5" /> Citations
                  </span>
                  <span className="text-3xl font-extrabold mt-1">{Math.round(selectedRun.category_scores.citation * 100)}%</span>
                </div>
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(selectedRun.category_scores.tool_success)}`}>
                  <span className="text-[10px] uppercase font-mono tracking-wider font-bold opacity-80 flex items-center gap-1">
                    <Wrench className="w-3.5 h-3.5" /> Tool Success
                  </span>
                  <span className="text-3xl font-extrabold mt-1">{Math.round(selectedRun.category_scores.tool_success * 100)}%</span>
                </div>
                <div className={`p-4 rounded-xl border flex flex-col justify-between ${getScoreColor(selectedRun.category_scores.latency)}`}>
                  <span className="text-[10px] uppercase font-mono tracking-wider font-bold opacity-80 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> Latency
                  </span>
                  <span className="text-3xl font-extrabold mt-1">{Math.round(selectedRun.category_scores.latency * 100)}%</span>
                </div>
              </div>

              {/* Recommendations list */}
              {selectedRun.results.length > 0 && (
                <div className="glass-card">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center gap-2">
                    <Activity className="w-4.5 h-4.5 text-brand-primary" /> Evaluation Recommendations
                  </h3>
                  <div className="space-y-2.5">
                    {selectedRun.results[0].recommendations.map((rec, idx) => (
                      <div key={idx} className="flex gap-2 text-xs text-gray-300 items-start">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-primary mt-1.5 shrink-0" />
                        <p>{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed cases table */}
              <div>
                <h2 className="text-lg font-semibold tracking-wide uppercase text-gray-400 mb-4 flex items-center gap-2">
                  Test Case Results Breakdown
                </h2>
                
                <div className="space-y-4">
                  {selectedRun.results.map((res, idx) => (
                    <div key={idx} className="glass-card p-0 overflow-hidden">
                      {/* Case header bar */}
                      <div 
                        onClick={() => setDetailsIdx(detailsIdx === idx ? null : idx)}
                        className="px-6 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#0E1322] cursor-pointer hover:bg-brand-surface/20 transition-all border-b border-brand-border/40"
                      >
                        <div className="min-w-0 flex-1">
                          <span className="text-xs font-semibold text-brand-accent block mb-1">CASE #{idx + 1} - Question</span>
                          <span className="text-sm font-semibold text-white truncate block">{res.question}</span>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <span className={`px-2.5 py-1 text-xs font-mono font-bold rounded-lg border ${getScoreColor(res.overall_score)}`}>
                            QA Score: {Math.round(res.overall_score * 100)}%
                          </span>
                          <span className={`w-2 h-2 rounded-full ${res.metrics.citations.success && !res.metrics.citations.fabricated_citations.length ? 'bg-green-400' : 'bg-red-400'}`} title="Citation Guard" />
                        </div>
                      </div>

                      {/* Case details drawer */}
                      {detailsIdx === idx && (
                        <div className="p-6 space-y-4 bg-brand-background/10 border-t border-brand-border/40 text-xs">
                          {/* Answer */}
                          <div className="space-y-1.5">
                            <span className="font-semibold text-gray-400 block font-mono">GENERATED ANSWER:</span>
                            <p className="p-3 bg-brand-surface/50 border border-brand-border/30 rounded-xl text-gray-300 leading-relaxed font-mono">
                              {res.answer}
                            </p>
                          </div>

                          {/* Metric scores breakdown */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                            {/* Citation metrics */}
                            <div className="space-y-2.5 p-4 border border-brand-border/50 rounded-xl bg-brand-surface/20">
                              <span className="font-bold text-white block uppercase tracking-wider border-b border-brand-border/30 pb-1.5">Citations & Hallucination report</span>
                              <div className="space-y-1.5">
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Broken References:</span>
                                  <span className={res.metrics.citations.broken_citations.length > 0 ? 'text-red-400 font-bold' : 'text-green-400'}>
                                    {res.metrics.citations.broken_citations.length > 0 ? res.metrics.citations.broken_citations.join(', ') : 'None'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Fabricated Citations:</span>
                                  <span className={res.metrics.citations.fabricated_citations.length > 0 ? 'text-red-400 font-bold' : 'text-green-400'}>
                                    {res.metrics.citations.fabricated_citations.length > 0 ? res.metrics.citations.fabricated_citations.join(', ') : 'None'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Duplicate Citation tags:</span>
                                  <span className={res.metrics.citations.duplicate_citations.length > 0 ? 'text-yellow-400' : 'text-green-400'}>
                                    {res.metrics.citations.duplicate_citations.length > 0 ? res.metrics.citations.duplicate_citations.join(', ') : 'None'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Response Groundedness:</span>
                                  <span className="text-white font-semibold">{Math.round(res.category_scores.groundedness * 100)}%</span>
                                </div>
                              </div>
                            </div>

                            {/* Performance metrics */}
                            <div className="space-y-2.5 p-4 border border-brand-border/50 rounded-xl bg-brand-surface/20">
                              <span className="font-bold text-white block uppercase tracking-wider border-b border-brand-border/30 pb-1.5">Performance & Latency</span>
                              <div className="space-y-1.5">
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Retrieval Recall:</span>
                                  <span className="text-white font-semibold">{Math.round(res.metrics.retrieval.recall * 100)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Retrieval Precision:</span>
                                  <span className="text-white font-semibold">{Math.round(res.metrics.retrieval.precision * 100)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Mean Reciprocal Rank (MRR):</span>
                                  <span className="text-white font-semibold">{res.metrics.retrieval.mrr}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">RAG Correctness:</span>
                                  <span className="text-white font-semibold">{Math.round(res.category_scores.correctness * 100)}%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Total Latency:</span>
                                  <span className="text-white font-mono">{res.metrics.total_latency_ms.toFixed(0)}ms</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
