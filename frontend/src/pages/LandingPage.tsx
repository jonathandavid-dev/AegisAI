import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield, ArrowRight, FileText, Database, Brain, Sparkles, ChevronDown, CheckCircle, MessageSquare } from 'lucide-react';
import { CinematicBackdrop } from '../components/ui/CinematicBackdrop';
import { ChatPage } from './ChatPage';

export const LandingPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Reasoning query simulation state
  const [typingText, setTypingText] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [queryStarted, setQueryStarted] = useState(false);
  const [answerStarted, setAnswerStarted] = useState(false);

  const sections = [
    { id: 'hero', label: 'Monolith', title: 'Chaos' },
    { id: 'documents', label: 'Documents', title: 'Knowledge' },
    { id: 'processing', label: 'Processing', title: 'Understanding' },
    { id: 'graph', label: 'Network', title: 'Reasoning' },
    { id: 'chat', label: 'Operating System', title: 'Action' }
  ];

  // Handle scroll detection for steps
  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const scrollPos = window.scrollY;
      const height = window.innerHeight;
      const index = Math.min(
        Math.max(Math.round(scrollPos / height), 0),
        sections.length - 1
      );
      setActiveSection(index);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Simulating query in Section 4 (Reasoning)
  useEffect(() => {
    if (activeSection === 3 && !queryStarted) {
      setQueryStarted(true);
      simulateQuery();
    }
  }, [activeSection]);

  const simulateQuery = () => {
    const query = "What is our corporate data security policy?";
    const answer = "Grounded response: All data must be encrypted at rest (AES-256) and in transit (TLS 1.3). Access requires multi-factor authentication (MFA) via Aegis Gateway.";
    
    let qIdx = 0;
    let aIdx = 0;
    
    const typeQuery = setInterval(() => {
      if (qIdx < query.length) {
        setTypingText((prev) => prev + query[qIdx]);
        qIdx++;
      } else {
        clearInterval(typeQuery);
        setTimeout(() => {
          setAnswerStarted(true);
          const typeAnswer = setInterval(() => {
            if (aIdx < answer.length) {
              setAnswerText((prev) => prev + answer[aIdx]);
              aIdx++;
            } else {
              clearInterval(typeAnswer);
            }
          }, 30);
        }, 1000);
      }
    }, 45);
  };

  const handleScrollTo = (index: number) => {
    window.scrollTo({
      top: index * window.innerHeight,
      behavior: 'smooth'
    });
  };

  return (
    <div ref={containerRef} className="relative min-h-[500vh] bg-black text-white font-sans overflow-x-hidden select-none">
      {/* Background System */}
      <div className="fixed inset-0 z-0">
        <CinematicBackdrop />
      </div>

      {/* Floating Glass Navigation Header */}
      <header className="fixed top-0 left-0 right-0 h-16 z-50 flex items-center justify-between px-8 bg-black/25 backdrop-blur-md border-b border-brand-border/20">
        <div className="flex items-center gap-3">
          <Shield className="w-5.5 h-5.5 text-brand-primary animate-pulse" />
          <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-white to-brand-primary bg-clip-text text-transparent">
            AegisAI
          </span>
        </div>
        <div className="flex items-center gap-4">
          <a 
            href="#story" 
            onClick={(e) => { e.preventDefault(); handleScrollTo(1); }}
            className="text-xs font-semibold text-brand-textSecondary hover:text-white transition-colors"
          >
            Narrative
          </a>
          <button
            onClick={() => navigate(user ? '/dashboard' : '/login')}
            className="px-4 py-1.5 border border-brand-primary/40 hover:border-brand-primary rounded-xl text-xs font-bold text-white bg-brand-primary/10 hover:bg-brand-primary/20 transition-all cursor-pointer"
          >
            {user ? 'Open Console' : 'Access Gateway'}
          </button>
        </div>
      </header>

      {/* Narrative Progress Stepper */}
      <div className="fixed right-8 top-1/2 -translate-y-1/2 z-40 hidden md:flex flex-col gap-6 items-center">
        {sections.map((sec, idx) => (
          <button
            key={sec.id}
            onClick={() => handleScrollTo(idx)}
            className="group flex items-center gap-3 focus:outline-none text-right cursor-pointer"
          >
            <span className={`text-[9px] font-mono font-bold uppercase tracking-widest transition-all duration-300 ${
              activeSection === idx ? 'text-brand-primary scale-105' : 'text-brand-textMuted opacity-0 group-hover:opacity-100'
            }`}>
              {sec.title}
            </span>
            <span className={`w-2 h-2 rounded-full border transition-all duration-300 ${
              activeSection === idx 
                ? 'bg-brand-primary border-brand-primary scale-125 shadow-[0_0_10px_#10B981]' 
                : 'border-brand-border hover:border-brand-textMuted bg-transparent'
            }`} />
          </button>
        ))}
      </div>

      {/* ====================================================
          SCENE 0: MONOLITH (Chaos -> Knowledge)
          ==================================================== */}
      <section className="h-screen w-screen relative flex flex-col items-center justify-center text-center px-6 z-10">
        <div className="space-y-6 max-w-3xl animate-fade-in-up">
          <div className="flex justify-center mb-6">
            {/* The Intelligence Monolith */}
            <div className="relative w-28 h-56 bg-gradient-to-b from-[#0b0c10] via-black to-[#050505] border-2 border-brand-primary/30 rounded-2xl flex items-center justify-center shadow-[0_0_40px_rgba(16,185,129,0.15)] transition-all duration-700 hover:border-brand-primary/60 hover:scale-105 group overflow-hidden">
              {/* Pulsing energy core */}
              <div className="absolute inset-x-0 top-1/4 bottom-1/4 bg-gradient-to-b from-brand-primary/40 via-transparent to-brand-primary/40 blur-xl animate-pulse" />
              {/* Inner details */}
              <div className="w-px h-full bg-gradient-to-b from-transparent via-brand-primary/40 to-transparent" />
              <Brain className="w-8 h-8 text-brand-primary animate-pulse relative z-10" />
              
              {/* Micro-spark particles */}
              <div className="absolute top-1/3 left-4 w-1.5 h-1.5 rounded-full bg-brand-accent animate-ping" />
              <div className="absolute bottom-1/4 right-5 w-1 h-1 rounded-full bg-brand-primary animate-ping" style={{ animationDelay: '1s' }} />
            </div>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Every Document.<br/>
            <span className="bg-gradient-to-r from-white via-brand-accent to-brand-primary bg-clip-text text-transparent">One Intelligence.</span>
          </h1>
          <p className="text-sm md:text-base text-brand-textSecondary max-w-xl mx-auto font-mono">
            Transform enterprise knowledge silos into a fully structured, queryable neural grid.
          </p>

          <div className="pt-4 flex justify-center gap-4">
            <button 
              onClick={() => handleScrollTo(1)}
              className="px-6 py-3 bg-gradient-to-r from-brand-primary to-brand-primaryHover text-white rounded-xl text-xs font-bold uppercase tracking-wider hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all cursor-pointer flex items-center gap-2"
            >
              Begin Journey <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="absolute bottom-8 animate-bounce">
          <ChevronDown className="w-5 h-5 text-brand-textMuted" />
        </div>
      </section>

      {/* ====================================================
          SCENE 1: DOCUMENTS (Knowledge)
          ==================================================== */}
      <section className="h-screen w-screen relative flex items-center justify-center px-8 z-10">
        <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className={`space-y-4 transition-all duration-700 ${activeSection === 1 ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}`}>
            <span className="text-[10px] font-mono text-brand-primary uppercase tracking-widest font-bold">Stage 01 // Input</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-white">Enter the Silo</h2>
            <p className="text-xs text-brand-textSecondary leading-relaxed">
              Documents are messy, fragmented, and locked in separate repositories. AegisAI ingests all formats seamlessly, mapping unstructured information into a unified memory space.
            </p>
          </div>

          <div className="relative h-64 flex items-center justify-center">
            {/* Floating files animation */}
            <div className={`absolute p-4 bg-brand-surface/80 border border-brand-border rounded-xl shadow-2xl transition-all duration-1000 ${
              activeSection >= 1 ? 'transform translate-x-[-80px] translate-y-[-40px] rotate-[-6deg]' : 'opacity-0 scale-50'
            }`}>
              <FileText className="w-8 h-8 text-[#EF4444] mb-2" />
              <div className="w-16 h-1.5 bg-white/20 rounded mb-1" />
              <div className="w-10 h-1.5 bg-white/10 rounded" />
            </div>

            <div className={`absolute p-4 bg-brand-surface/80 border border-brand-border rounded-xl shadow-2xl transition-all duration-1000 delay-150 ${
              activeSection >= 1 ? 'transform translate-x-[60px] translate-y-[-60px] rotate-[8deg]' : 'opacity-0 scale-50'
            }`}>
              <Database className="w-8 h-8 text-brand-primary mb-2" />
              <div className="w-14 h-1.5 bg-white/20 rounded mb-1" />
              <div className="w-12 h-1.5 bg-white/10 rounded" />
            </div>

            <div className={`absolute p-4 bg-brand-surface/80 border border-brand-border rounded-xl shadow-2xl transition-all duration-1000 delay-300 ${
              activeSection >= 1 ? 'transform translate-x-[-10px] translate-y-[50px] rotate-[2deg]' : 'opacity-0 scale-50'
            }`}>
              <Sparkles className="w-8 h-8 text-brand-accent mb-2" />
              <div className="w-20 h-1.5 bg-white/20 rounded mb-1" />
              <div className="w-8 h-1.5 bg-white/10 rounded" />
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================
          SCENE 2: PROCESSING (Understanding)
          ==================================================== */}
      <section className="h-screen w-screen relative flex items-center justify-center px-8 z-10">
        <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className="relative h-64 flex items-center justify-center order-last md:order-first">
            {/* Floating dissolving particles representing processing chunks */}
            <div className="w-48 h-48 border border-brand-primary/20 rounded-full flex items-center justify-center relative">
              <div className={`absolute w-36 h-36 border border-brand-accent/20 rounded-full animate-spin`} style={{ animationDuration: '8s' }} />
              <Database className="w-10 h-10 text-brand-primary animate-pulse" />
              
              {/* Particle streams */}
              {activeSection >= 2 && (
                <>
                  <div className="absolute top-2 left-10 w-2 h-2 bg-brand-primary rounded-full animate-ping" />
                  <div className="absolute bottom-6 right-8 w-1.5 h-1.5 bg-brand-accent rounded-full animate-ping" style={{ animationDelay: '0.5s' }} />
                  <div className="absolute top-1/2 right-2 w-1 h-1 bg-white rounded-full animate-ping" style={{ animationDelay: '1s' }} />
                </>
              )}
            </div>
          </div>

          <div className={`space-y-4 transition-all duration-700 ${activeSection === 2 ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-10'}`}>
            <span className="text-[10px] font-mono text-brand-primary uppercase tracking-widest font-bold">Stage 02 // Core</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-white">Synthesize to Chunks</h2>
            <p className="text-xs text-brand-textSecondary leading-relaxed">
              Files are automatically parsed, sliced into semantic code blocks, and transformed into dense vector embeddings. Raw text dissolves into operational vectors ready for inference.
            </p>
          </div>
        </div>
      </section>

      {/* ====================================================
          SCENE 3: KNOWLEDGE NETWORK (Reasoning)
          ==================================================== */}
      <section className="h-screen w-screen relative flex items-center justify-center px-8 z-10">
        <div className="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className={`space-y-4 transition-all duration-700 ${activeSection === 3 ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}`}>
            <span className="text-[10px] font-mono text-brand-primary uppercase tracking-widest font-bold">Stage 03 // Network</span>
            <h2 className="text-3xl md:text-4xl font-extrabold text-white">Neural Pathways</h2>
            <p className="text-xs text-brand-textSecondary leading-relaxed">
              Embeddings establish semantic relations, creating a live, interactive knowledge graph. As query signals pulse through the database, AegisAI maps context and draws precise conclusions.
            </p>
            {queryStarted && (
              <div className="p-3 bg-brand-surface border border-brand-border/60 rounded-xl font-mono text-[10px] text-brand-textSecondary space-y-1.5">
                <div className="flex items-center gap-1.5 text-white">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-ping" />
                  <span>SIGNAL DETECTED:</span>
                </div>
                <p className="text-brand-accent">Query: "{typingText}"</p>
                {answerStarted && <p className="text-white mt-1 leading-normal border-t border-brand-border/30 pt-1">Answer: {answerText}</p>}
              </div>
            )}
          </div>

          <div className="relative h-72 flex items-center justify-center">
            {/* SVG Interactive Neural Network Graph */}
            <svg width="280" height="280" viewBox="0 0 200 200" className="text-brand-primary/30">
              <line x1="100" y1="100" x2="40" y2="40" stroke="currentColor" strokeWidth="1" className={activeSection >= 3 ? "animate-pulse" : ""} />
              <line x1="100" y1="100" x2="160" y2="50" stroke="currentColor" strokeWidth="1" />
              <line x1="100" y1="100" x2="140" y2="150" stroke="currentColor" strokeWidth="1" />
              <line x1="100" y1="100" x2="50" y2="150" stroke="currentColor" strokeWidth="1" />
              <line x1="40" y1="40" x2="160" y2="50" stroke="currentColor" strokeWidth="0.5" />
              <line x1="140" y1="150" x2="50" y2="150" stroke="currentColor" strokeWidth="0.5" />
              
              {/* Nodes */}
              <circle cx="100" cy="100" r="8" className="fill-brand-primary text-brand-primary hover:scale-125 transition-transform" />
              <circle cx="40" cy="40" r="5" className="fill-brand-accent" />
              <circle cx="160" cy="50" r="5" className="fill-brand-accent" />
              <circle cx="140" cy="150" r="5" className="fill-brand-primary" />
              <circle cx="50" cy="150" r="5" className="fill-brand-accent" />
            </svg>
          </div>
        </div>
      </section>

      {/* ====================================================
          SCENE 4: CONVERSATION (Action)
          ==================================================== */}
      <section className="h-screen w-screen relative flex flex-col items-center justify-center p-6 z-10">
        <div className="w-full max-w-5xl h-[85vh] glass-card p-0 flex flex-col overflow-hidden relative shadow-[0_0_50px_rgba(16,185,129,0.06)] border border-brand-primary/20">
          <div className="absolute inset-0 z-0 bg-black/60 pointer-events-none" />
          
          {/* Header to direct user inside frame */}
          <div className="absolute top-4 left-4 right-4 z-20 flex justify-between items-center pointer-events-auto">
            <span className="text-[9px] font-mono bg-brand-primary/10 border border-brand-primary/30 text-brand-primary px-2.5 py-1 rounded-xl uppercase tracking-widest font-bold flex items-center gap-1.5 select-none">
              <MessageSquare className="w-3.5 h-3.5" /> Stage 04 // Interactive Operating System Terminal
            </span>
            <button
              onClick={() => navigate(user ? '/dashboard' : '/login')}
              className="text-[9px] font-bold uppercase tracking-wider text-brand-textSecondary hover:text-white border border-brand-border px-3 py-1.5 rounded-xl hover:bg-brand-surface transition-colors"
            >
              Launch Console
            </button>
          </div>

          <div className="flex-1 h-full pt-14 relative z-10 pointer-events-auto">
            {/* Embed real RAG Chat experience page inside landing story only if logged in, otherwise mock chat */}
            {user ? (
              <ChatPage />
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-4 font-mono select-none">
                <Brain className="w-10 h-10 text-brand-primary animate-pulse" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">AegisAI Cognitive Sandbox</h3>
                <p className="text-xs text-brand-textSecondary max-w-sm leading-relaxed">
                  The live interactive RAG console requires gateway validation. Please sign in to establish an active session container.
                </p>
                <div className="pt-2">
                  <Link
                    to="/login"
                    className="px-6 py-2.5 bg-gradient-to-r from-brand-primary to-brand-primaryHover text-white rounded-xl text-xs font-bold uppercase tracking-wider hover:shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all inline-block"
                  >
                    Authenticate Session
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};
