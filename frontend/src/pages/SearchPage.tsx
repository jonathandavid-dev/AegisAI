import React, { useState } from 'react';
import api from '../services/api';
import { 
  Search, 
  SlidersHorizontal, 
  BookOpen, 
  Layers, 
  HelpCircle, 
  Loader2, 
  X,
  FileText,
  Clock,
  ExternalLink
} from 'lucide-react';

interface SearchResult {
  document_id: number;
  chunk_id: str;
  filename: string;
  page_number: number;
  chunk_index: number;
  score: number;
  content: string;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  processing_time_ms: number;
}

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [timeMs, setTimeMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Advanced Filters
  const [threshold, setThreshold] = useState(0.50);
  const [topK, setTopK] = useState(10);
  const [filterFilename, setFilterFilename] = useState('');
  const [filterPage, setFilterPage] = useState('');

  // Preview Drawer Modal
  const [previewItem, setPreviewItem] = useState<SearchResult | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const filtersPayload: Record<string, any> = {
        similarity_threshold: threshold
      };

      if (filterFilename.trim()) {
        filtersPayload['filename'] = filterFilename.trim();
      }
      if (filterPage.trim()) {
        filtersPayload['page_number'] = parseInt(filterPage.trim(), 10);
      }

      // Call advanced search to support custom similarity threshold filters
      const response = await api.post<SearchResponse>('/search/advanced', {
        query: query.trim(),
        top_k: topK,
        filters: filtersPayload
      });

      setResults(response.data.results);
      setTimeMs(response.data.processing_time_ms);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || 'An error occurred during search retrieval.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Helper to highlight search query terms in the snippet
  const highlightText = (text: string, searchTerms: string) => {
    if (!searchTerms.trim()) return text;
    const terms = searchTerms.split(/\s+/).filter(t => t.length > 1);
    if (terms.length === 0) return text;
    
    // Create regex matching any of the query terms case insensitively
    const pattern = `(${terms.map(t => t.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')).join('|')})`;
    const regex = new RegExp(pattern, 'gi');
    
    const parts = text.split(regex);
    return (
      <>
        {parts.map((part, i) => 
          regex.test(part) ? (
            <mark key={i} className="bg-brand-primary/30 text-white font-semibold rounded px-0.5 border-b border-brand-primary/50">
              {part}
            </mark>
          ) : part
        )}
      </>
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-400 border-green-500/30 bg-green-500/10';
    if (score >= 0.8) return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
    return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Search Header Banner */}
      <div className="glass-card flex items-center justify-between py-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Cognitive Search Engine</h1>
          <p className="text-gray-400 text-sm">Perform fast cosine-similarity semantic vector searches across your knowledge base documents.</p>
        </div>
        <div className="w-16 h-16 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary hidden sm:flex">
          <Search className="w-8 h-8" />
        </div>
      </div>

      {/* Main Search Panel */}
      <div className="glass-card space-y-4">
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query or ask a semantic question..."
              className="w-full pl-12 pr-4 py-3 bg-brand-background border border-brand-border/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary/80 focus:ring-1 focus:ring-brand-primary/50 transition-all font-sans text-base"
              disabled={loading}
            />
          </div>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`p-3 border rounded-xl flex items-center justify-center transition-all ${
              showFilters 
                ? 'bg-brand-primary/10 border-brand-primary text-brand-primary' 
                : 'border-brand-border/60 text-gray-400 hover:text-white hover:border-gray-600'
            }`}
            title="Toggle Search Filters"
          >
            <SlidersHorizontal className="w-5 h-5" />
          </button>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-gradient-to-r from-brand-primary to-brand-accent text-white font-medium rounded-xl hover:opacity-90 transition-opacity flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-base"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> Retrieving...
              </>
            ) : (
              <>
                Search
              </>
            )}
          </button>
        </form>

        {/* Collapsible Advanced Filters Section */}
        {showFilters && (
          <div className="p-4 border border-brand-border/40 rounded-xl bg-brand-background/40 grid grid-cols-1 md:grid-cols-4 gap-4 animate-fade-in">
            {/* Threshold Slider */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono flex justify-between">
                <span>Min Similarity</span>
                <span className="text-brand-primary">{(threshold * 100).toFixed(0)}%</span>
              </label>
              <input
                type="range"
                min="0.5"
                max="1.0"
                step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full accent-brand-primary cursor-pointer bg-brand-border h-1.5 rounded-lg appearance-none"
              />
            </div>

            {/* Top K Limit Slider */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono flex justify-between">
                <span>Top K Results</span>
                <span className="text-brand-accent">{topK} chunks</span>
              </label>
              <input
                type="range"
                min="5"
                max="50"
                step="1"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                className="w-full accent-brand-accent cursor-pointer bg-brand-border h-1.5 rounded-lg appearance-none"
              />
            </div>

            {/* Filename Input */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono">Filename Scope</label>
              <input
                type="text"
                value={filterFilename}
                onChange={(e) => setFilterFilename(e.target.value)}
                placeholder="e.g. document.pdf"
                className="w-full px-3 py-1.5 bg-brand-background border border-brand-border/40 rounded-lg text-xs text-white focus:outline-none focus:border-brand-primary"
              />
            </div>

            {/* Page Number Input */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono">Target Page</label>
              <input
                type="number"
                min="1"
                value={filterPage}
                onChange={(e) => setFilterPage(e.target.value)}
                placeholder="e.g. 3"
                className="w-full px-3 py-1.5 bg-brand-background border border-brand-border/40 rounded-lg text-xs text-white focus:outline-none focus:border-brand-primary"
              />
            </div>
          </div>
        )}
      </div>

      {/* Error Output */}
      {error && (
        <div className="p-4 border border-red-500/20 bg-red-500/5 rounded-xl text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Results Section */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <Loader2 className="w-10 h-10 text-brand-primary animate-spin" />
          <span className="text-xs text-gray-400 font-mono uppercase tracking-wider">Embedding Query & Matching Vectors...</span>
        </div>
      ) : results !== null ? (
        <div className="space-y-4">
          {/* Query Stats Header */}
          <div className="flex justify-between items-center text-xs text-gray-400 font-mono">
            <span>RETRIEVED {results.length} CANDIDATE MATCHES</span>
            {timeMs !== null && (
              <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> QUERY SOLVED IN {timeMs.toFixed(1)} MS</span>
            )}
          </div>

          {/* Results Cards List */}
          {results.length === 0 ? (
            <div className="text-center py-16 border border-brand-border/30 border-dashed rounded-2xl bg-brand-surface/10">
              <HelpCircle className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <span className="text-sm font-semibold text-white block">No relevant chunks found</span>
              <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                No vector records exceeded the similarity threshold. Try adjusting the Min Similarity filter slider.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((result, index) => (
                <div key={result.chunk_id} className="glass-card hover:border-brand-border transition-colors space-y-3 relative overflow-hidden group">
                  {/* Card Header stats */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-brand-border/20 pb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 border rounded text-[10px] uppercase font-bold font-mono ${getScoreColor(result.score)}`}>
                        {(result.score * 100).toFixed(1)}% Match
                      </span>
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-semibold bg-brand-background text-gray-300 border border-brand-border/40 truncate max-w-xs">
                        <FileText className="w-3 h-3 text-brand-primary" /> {result.filename}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-gray-400 font-mono">
                      <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" /> Page {result.page_number}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1"><Layers className="w-3 h-3" /> Chunk {result.chunk_index}</span>
                    </div>
                  </div>

                  {/* Text Content */}
                  <p className="text-gray-300 text-sm leading-relaxed font-sans font-light select-text">
                    {highlightText(result.content, query)}
                  </p>

                  {/* Card Action footer */}
                  <div className="flex justify-between items-center pt-2">
                    <span className="text-[10px] text-gray-500 font-mono uppercase">ID: {result.chunk_id}</span>
                    <button
                      onClick={() => setPreviewItem(result)}
                      className="text-xs text-brand-primary hover:text-brand-accent transition-colors font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                    >
                      Preview Segment <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        // Initial Empty State
        <div className="text-center py-20 border border-brand-border/20 border-dashed rounded-2xl bg-brand-surface/5">
          <Search className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <span className="text-sm font-semibold text-white block">AegisAI Semantic Index Solver</span>
          <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
            Input a question above. The engine will embed your query and perform a semantic search against the persistent ChromaDB collection.
          </p>
        </div>
      )}

      {/* Details Preview Modal */}
      {previewItem && (
        <div className="fixed inset-0 bg-brand-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto relative animate-scale-up border border-brand-primary/30">
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-brand-border/40 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <FileText className="text-brand-primary w-5 h-5" /> Segment Details
                </h3>
                <span className="text-[10px] font-mono text-gray-400 mt-0.5 block truncate max-w-md">ID: {previewItem.chunk_id}</span>
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Document metadata table */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-brand-background/40 p-3 border border-brand-border/40 rounded-xl font-mono text-xs text-gray-300">
              <div>
                <span className="text-[10px] text-gray-500 block">FILENAME</span>
                <span className="font-semibold text-white truncate block">{previewItem.filename}</span>
              </div>
              <div>
                <span className="text-[10px] text-gray-500 block">PAGE</span>
                <span className="font-semibold text-white block">{previewItem.page_number}</span>
              </div>
              <div>
                <span className="text-[10px] text-gray-500 block">INDEX</span>
                <span className="font-semibold text-white block">{previewItem.chunk_index}</span>
              </div>
              <div>
                <span className="text-[10px] text-gray-500 block">MATCH SCORE</span>
                <span className="font-semibold text-brand-primary block">{(previewItem.score * 100).toFixed(1)}%</span>
              </div>
            </div>

            {/* Chunk text content */}
            <div className="space-y-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-gray-500 block">Full Segment Text</span>
              <div className="bg-brand-background border border-brand-border/40 rounded-xl p-4 max-h-[40vh] overflow-y-auto text-sm text-gray-300 font-sans leading-relaxed whitespace-pre-wrap select-text">
                {previewItem.content}
              </div>
            </div>

            {/* Close footer */}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setPreviewItem(null)}
                className="px-4 py-2 border border-brand-border/60 text-gray-300 font-medium rounded-xl hover:text-white hover:border-gray-400 transition-colors text-xs"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
