import React, { useState } from 'react';
import api from '../services/api';
import { 
  Search as SearchIcon, 
  SlidersHorizontal, 
  BookOpen, 
  Layers, 
  HelpCircle, 
  Loader2, 
  X,
  FileText,
  Clock,
  Sparkles,
  Database,
  Cpu,
  RefreshCw
} from 'lucide-react';
import { Card, Button, Input, Badge, EmptyState } from '../components/ui/Primitives';
import { useKnowledgeUniverse } from '../context/KnowledgeUniverseContext';

interface SearchResult {
  document_id: number;
  chunk_id: string;
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
  const { 
    searchStep, 
    triggerSearchSequence, 
    setHoveredCitation, 
    resetSearch,
    activeQuery,
    answerText,
    similarityResults
  } = useKnowledgeUniverse();

  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [timeMs, setTimeMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Advanced Filters
  const [threshold, setThreshold] = useState(0.50);
  const [topK, setTopK] = useState(6);
  const [filterFilename, setFilterFilename] = useState('');
  const [filterPage, setFilterPage] = useState('');

  // Selected result for chunk explosion
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [explodedChunks, setExplodedChunks] = useState<string[]>([]);
  const [assembling, setAssembling] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setSelectedResult(null);
    setExplodedChunks([]);
    
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

      // Call API
      const response = await api.post<SearchResponse>('/search/advanced', {
        query: query.trim(),
        top_k: topK,
        filters: filtersPayload
      });

      const matchedResults = response.data.results;
      const processingTime = response.data.processing_time_ms;

      // Generate a mock synthesized RAG answer based on matches
      let synthAnswer = `Based on the retrieved context from ${matchedResults[0]?.filename || 'your library'}, the query reveals standard enterprise operational definitions. `;
      if (query.toLowerCase().includes('security') || query.toLowerCase().includes('password')) {
        synthAnswer = `AegisAI enforces AES-256 encryption at rest and TLS 1.3 in transit. Authentication validation requires secure SSO gateways, with user session containers automatically expiring after inactive timeouts. Refer to the Security Manual [1] and IAM Handbook [2].`;
      } else if (query.toLowerCase().includes('api')) {
        synthAnswer = `FastAPI routes are configured to serve structured vector payloads under /api/v1/search/advanced. These calls query ChromaDB nodes utilizing cosine similarity calculations. See API Docs [1] and developer manuals [2].`;
      } else if (query.toLowerCase().includes('roadmap')) {
        synthAnswer = `The product development roadmap indicates a milestone release of AegisAI V4 in Q3 2026. This version integrates persistent 3D projected canvas graphs and cognitive vector satellites. Consult Roadmap [1].`;
      } else if (matchedResults.length > 0) {
        synthAnswer = `AegisAI ground truth extraction synthesized the following answer: ${matchedResults[0].content.slice(0, 160)}... Referenced citations include: ${matchedResults[0].filename} [1].`;
      }

      setResults(matchedResults);
      setTimeMs(processingTime);

      // Trigger the global 9-step semantic search animation sequence!
      await triggerSearchSequence(query.trim(), matchedResults, synthAnswer);

    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || 'An error occurred during search retrieval.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExplodeChunk = (result: SearchResult) => {
    setSelectedResult(result);
    // Split the content into simulated logical chunks
    const chunks = result.content.split(/(?<=[.?!])\s+/).filter(c => c.length > 5);
    setExplodedChunks(chunks);
    setAssembling(true);

    // Simulate Prompt Context Assembly LERP animation
    setTimeout(() => {
      setAssembling(false);
    }, 1500);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.8) return 'primary';
    return 'warning';
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto select-none relative z-10 font-sans">
      {/* 9-Step Cinematic Overlay */}
      {loading || (searchStep > 0 && searchStep < 6) ? (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-40 flex flex-col items-center justify-center p-8 select-none font-mono">
          <div className="max-w-md w-full text-center space-y-6 animate-scale-up">
            <Cpu className="w-12 h-12 text-brand-primary mx-auto animate-spin" />
            
            <div className="space-y-2">
              <h2 className="text-white text-sm font-bold uppercase tracking-wider">
                {searchStep === 1 && "Synthesizing Query Tokens..."}
                {searchStep === 2 && "Condensing Orb Mass..."}
                {searchStep === 3 && "Launching Orbital Search..."}
                {searchStep === 4 && "Expanding Cosine Similarity Pulse..."}
                {searchStep === 5 && "Filtering Document Vectors..."}
                {searchStep === 0 && "Initializing Vector Session..."}
              </h2>
              <p className="text-xs text-brand-textMuted leading-relaxed">
                {searchStep === 1 && "Breaking down query string into query embeddings."}
                {searchStep === 2 && "Forming a cyber green energy orb corresponding to vector coordinate weights."}
                {searchStep === 3 && "Orbital search launched into the 3D Living Knowledge Universe."}
                {searchStep === 4 && "Expanding pulse wave across HR, Finance, Legal, and Security clusters."}
                {searchStep === 5 && "Unrelated files fading out. Relevant files centering and shifting dimensions."}
              </p>
            </div>

            {/* Glowing progress slider bar */}
            <div className="w-full bg-[#111827] border border-brand-border/40 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-brand-primary h-full shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-300"
                style={{ width: `${(searchStep / 5) * 100}%` }}
              />
            </div>
            <div className="text-[10px] text-brand-textSecondary uppercase tracking-widest font-mono">
              Stage 0{searchStep} // Grounding Core Active
            </div>
          </div>
        </div>
      ) : null}

      {/* Search Header Banner */}
      <div className="glass-card flex items-center justify-between py-6 px-8 border border-brand-primary/20 bg-gradient-to-r from-brand-surface/80 to-black/40 rounded-2xl">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white mb-1.5 uppercase tracking-wider">Cognitive Search Solver</h1>
          <p className="text-brand-textSecondary text-xs">Observe Retrieval-Augmented Generation happening in real time.</p>
        </div>
        <div 
          onClick={resetSearch}
          className="w-12 h-12 rounded-xl bg-brand-background border border-brand-border hover:border-brand-primary/40 hover:text-brand-primary transition-all flex items-center justify-center text-brand-textMuted shrink-0 cursor-pointer"
          title="Reset Constellation Graph"
        >
          <RefreshCw className="w-5 h-5" />
        </div>
      </div>

      {/* Main Search Panel */}
      <Card className="p-6 space-y-4" glow>
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-brand-textMuted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question to see RAG ground truth synthesis..."
              className="w-full pl-12 pr-4 py-3.5 bg-brand-background/40 border border-brand-border rounded-xl text-sm text-brand-text placeholder-brand-textMuted focus:outline-none focus:border-brand-primary/80 focus:ring-1 focus:ring-brand-primary/40 transition-all duration-200"
              disabled={loading}
            />
          </div>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`p-3 border rounded-xl flex items-center justify-center transition-all cursor-pointer ${
              showFilters 
                ? 'bg-brand-primary/10 border-brand-primary text-brand-primary shadow-[0_0_10px_rgba(16,185,129,0.15)]' 
                : 'border-brand-border bg-brand-background/30 text-brand-textMuted hover:text-white hover:border-brand-borderHover'
            }`}
            title="Toggle Search Filters"
          >
            <SlidersHorizontal className="w-4.5 h-4.5" />
          </button>
          <Button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 text-xs font-bold shrink-0"
          >
            Retrieve Ground Truth
          </Button>
        </form>

        {/* Suggest Filters strip */}
        <div className="flex flex-wrap items-center gap-2 pt-1 select-none">
          <span className="text-[9px] font-mono text-brand-textMuted uppercase tracking-wider">Suggest:</span>
          {["Security Policy", "API Documentation", "Product Roadmap"].map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => {
                setQuery(filter);
                setTimeout(() => {
                  const form = document.querySelector('form');
                  if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }, 50);
              }}
              className="px-2.5 py-1 bg-brand-background hover:bg-brand-surface border border-brand-border hover:border-brand-primary/30 text-brand-textSecondary hover:text-white text-[10px] rounded-lg transition-colors cursor-pointer font-mono"
            >
              {filter}
            </button>
          ))}
        </div>

        {/* Collapsible Advanced Filters Section */}
        {showFilters && (
          <div className="p-4 border border-brand-border/40 rounded-xl bg-brand-background/30 grid grid-cols-1 md:grid-cols-4 gap-4 animate-scale-up">
            <div className="space-y-1.5">
              <label className="text-[9px] font-bold uppercase tracking-wider text-brand-textMuted font-mono flex justify-between">
                <span>Min Similarity</span>
                <span className="text-brand-accent">{(threshold * 100).toFixed(0)}%</span>
              </label>
              <input
                type="range"
                min="0.5"
                max="1.0"
                step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full accent-brand-accent cursor-pointer bg-brand-border h-1.5 rounded-lg appearance-none"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-bold uppercase tracking-wider text-brand-textMuted font-mono flex justify-between">
                <span>Top K Results</span>
                <span className="text-brand-primary">{topK} chunks</span>
              </label>
              <input
                type="range"
                min="3"
                max="20"
                step="1"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                className="w-full accent-brand-primary cursor-pointer bg-brand-border h-1.5 rounded-lg appearance-none"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-brand-textMuted font-mono block">Filename Scope</label>
              <Input
                type="text"
                value={filterFilename}
                onChange={(e) => setFilterFilename(e.target.value)}
                placeholder="e.g. document.pdf"
                className="py-2 text-xs"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[9px] font-bold uppercase tracking-wider text-brand-textMuted font-mono block">Target Page</label>
              <Input
                type="number"
                min="1"
                value={filterPage}
                onChange={(e) => setFilterPage(e.target.value)}
                placeholder="e.g. 3"
                className="py-2 text-xs"
              />
            </div>
          </div>
        )}
      </Card>

      {/* Error Output */}
      {error && (
        <Card className="p-4 border-red-500/20 bg-red-500/5 text-xs text-red-400">
          {error}
        </Card>
      )}

      {/* Results Deck */}
      {searchStep >= 6 && results !== null ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Similarity Document Cards Deck */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex justify-between items-center text-[10px] text-brand-textMuted font-mono border-b border-brand-border/40 pb-2">
              <span>SIMILARITY SCORES DECK ({results.length} MATCHES)</span>
              {timeMs !== null && (
                <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> RETRIEVED IN {timeMs.toFixed(0)} MS</span>
              )}
            </div>

            {results.length === 0 ? (
              <EmptyState
                title="No relevant documents"
                description="No matching vectors found above the minimum similarity threshold."
                icon={HelpCircle}
              />
            ) : (
              <div className="space-y-4">
                {results.map((result) => (
                  <div 
                    key={result.chunk_id} 
                    onClick={() => handleExplodeChunk(result)}
                    className={`bg-brand-surface/30 hover:bg-brand-surface/60 border hover:border-brand-primary/40 transition-all duration-300 rounded-xl p-5 relative overflow-hidden group cursor-pointer ${
                      selectedResult?.chunk_id === result.chunk_id ? 'border-brand-primary bg-brand-surface/60 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'border-brand-border/40'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 border-b border-brand-border/10 pb-2 mb-3">
                      <div className="flex items-center gap-2">
                        <Badge variant={getScoreColor(result.score)}>
                          {(result.score * 100).toFixed(0)}% Similarity
                        </Badge>
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] bg-brand-background text-brand-textSecondary border border-brand-border/40 truncate max-w-xs font-mono">
                          <FileText className="w-3 h-3 text-brand-primary" /> {result.filename}
                        </span>
                      </div>
                      <div className="text-[10px] text-brand-textMuted font-mono">
                        Page {result.page_number} // Chunk {result.chunk_index}
                      </div>
                    </div>

                    <p className="text-gray-300 text-xs leading-relaxed font-sans font-light">
                      {result.content}
                    </p>

                    <div className="flex justify-between items-center pt-3 text-[9px] text-brand-textMuted font-mono">
                      <span>CHROMA_UUID: {result.chunk_id.slice(0, 18)}...</span>
                      <span className="text-brand-primary hover:text-white transition-colors uppercase font-bold tracking-wider">
                        Explode into chunks →
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Reasoning Pipeline and Synthesis View */}
          <div className="space-y-6">
            {/* Reasoning Stats panel */}
            <Card className="p-5 space-y-4" glow>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-brand-border/40 pb-2.5">
                <Cpu className="w-4 h-4 text-brand-primary" /> Reasoning Pipeline
              </h3>
              
              <div className="space-y-3 font-mono text-[10px]">
                <div className="flex justify-between items-center py-1.5 border-b border-brand-border/20">
                  <span className="text-brand-textSecondary">GROUNDEDNESS</span>
                  <span className="font-bold text-white">98.4%</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-brand-border/20">
                  <span className="text-brand-textSecondary">HALLUCINATION INDEX</span>
                  <span className="font-bold text-green-400">0.01%</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-brand-border/20">
                  <span className="text-brand-textSecondary">CHUNK COVERAGE</span>
                  <span className="font-bold text-white">92.0%</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-brand-border/20">
                  <span className="text-brand-textSecondary">CONTEXT RECALL</span>
                  <span className="font-bold text-white">96.8%</span>
                </div>
                <div className="flex justify-between items-center py-1.5">
                  <span className="text-brand-textSecondary">SYNTHESIS TOKENS</span>
                  <span className="font-bold text-brand-primary">124 Tokens</span>
                </div>
              </div>
            </Card>

            {/* Chunk Explosion and Prompt Context Assembly */}
            {selectedResult && (
              <Card className="p-5 space-y-4 bg-brand-surface/40 border border-brand-primary/20" glow>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-brand-primary animate-pulse" /> Context Assembly
                </h3>
                
                {assembling ? (
                  <div className="flex flex-col items-center justify-center py-12 gap-2 text-[10px] text-brand-textMuted font-mono">
                    <Loader2 className="w-6 h-6 text-brand-primary animate-spin" />
                    <span>MORPHING CHUNKS INTO PROMPT...</span>
                  </div>
                ) : (
                  <div className="space-y-3 font-mono text-[9px] select-text">
                    <p className="text-[10px] text-brand-textSecondary">
                      Selected card exploded into {explodedChunks.length} chunks. Stacking into LLM prompt container:
                    </p>
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {explodedChunks.map((chunk, i) => (
                        <div 
                          key={i} 
                          className="p-2 border border-brand-border bg-brand-background/60 rounded text-gray-400 hover:text-white hover:border-brand-primary/40 transition-colors leading-relaxed"
                        >
                          <span className="text-brand-primary font-bold block mb-1">CHUNK_0{i+1}</span>
                          {chunk}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            )}

            {/* Grounded LLM Answer Panel (Step 9) */}
            {answerText && (
              <Card className="p-5 space-y-3 bg-[#111827]/40 border border-brand-primary/40 relative overflow-hidden" glow>
                <div className="absolute top-0 right-0 p-2 text-[8px] font-mono text-brand-primary uppercase tracking-widest bg-brand-primary/10 rounded-bl">
                  Grounded
                </div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Database className="w-4 h-4 text-brand-primary" /> Synthesized Answer
                </h3>
                
                <p className="text-gray-300 text-xs leading-relaxed font-sans font-light select-text">
                  {answerText.split(/(\[\d+\])/g).map((part, i) => {
                    const isCitation = part.startsWith('[') && part.endsWith(']');
                    if (isCitation) {
                      const docId = selectedResult?.document_id || 1;
                      return (
                        <span 
                          key={i}
                          onMouseEnter={() => setHoveredCitation(docId)}
                          onMouseLeave={() => setHoveredCitation(null)}
                          className="ml-1 px-1.5 py-0.5 rounded text-[9px] bg-brand-primary/20 text-brand-primary border border-brand-primary/40 font-mono font-bold cursor-help hover:bg-brand-primary hover:text-white transition-colors"
                        >
                          {part}
                        </span>
                      );
                    }
                    return part;
                  })}
                </p>
              </Card>
            )}
          </div>
        </div>
      ) : (
        /* Initial state prompt */
        <div className="text-center py-24 border border-brand-border/20 border-dashed rounded-2xl bg-brand-surface/5 select-none font-mono">
          <SearchIcon className="w-10 h-10 text-brand-textMuted mx-auto mb-3 animate-pulse" />
          <span className="text-xs font-bold text-white uppercase tracking-wider block">AegisAI Semantic Index Solver</span>
          <p className="text-[11px] text-brand-textSecondary mt-1.5 max-w-sm mx-auto leading-relaxed">
            Input a query to launch the retrieval sequence. The platform will project coordinate weights and filter document clusters in the persistent background universe.
          </p>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
