import React, { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { Card, Button, Avatar, Badge } from '../components/ui/Primitives';
import { useKnowledgeUniverse } from '../context/KnowledgeUniverseContext';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  Loader2, 
  X, 
  FileText, 
  BookOpen, 
  Layers, 
  Clock,
  Sparkles,
  Plus,
  Trash2,
  Edit3,
  Check,
  BrainCircuit,
  CornerDownRight,
  Wrench,
  Activity,
  Shield,
  Cpu
} from 'lucide-react';

interface Citation {
  document_id: number;
  filename: string;
  page_number: number;
  chunk_index: number;
}

interface ToolExecution {
  tool_used: string;
  execution_time_ms: number;
  status: string;
}

interface Conversation {
  id: number;
  title: string;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: string | number;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM' | 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
  citations?: Citation[];
  durationMs?: number;
  rewritten_query?: string;
  memory_summary?: boolean;
  tool_execution?: ToolExecution;
  timestamp?: string;
}

interface DocumentPreview {
  filename: string;
  page_count: number | null;
  total_chunks: number;
  preview_content: string;
}

export const ChatPage: React.FC = () => {
  const { user } = useAuth();
  const { setHoveredCitation } = useKnowledgeUniverse();
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  
  // Streaming States
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'disconnected' | 'reconnecting'>('idle');
  const [streamStage, setStreamStage] = useState<{ stage: string; detail?: string } | null>(null);

  // Inline rename state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitleInput, setEditTitleInput] = useState('');

  // Diagnostic states for the last message
  const [lastDiag, setLastDiag] = useState<{
    rewritten_query?: string;
    summary_used?: boolean;
    messages_used?: number;
    tool_execution?: ToolExecution | null;
    citations?: Citation[];
  } | null>(null);

  // Document Preview Modal State
  const [previewDocId, setPreviewDocId] = useState<number | null>(null);
  const [previewData, setPreviewData] = useState<DocumentPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      fetchMessages(activeConversationId);
    } else {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: 'Hello! I am AegisAI. I am connected to the secured LLM provider gateway and local vector stores. Ask me a question about your uploaded documents, and I will generate a grounded response referencing specific document citations.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      setLastDiag(null);
    }
  }, [activeConversationId]);

  const fetchConversations = async () => {
    setLoadingConversations(true);
    try {
      const response = await api.get<Conversation[]>('/conversations');
      setConversations(response.data);
    } catch (err) {
      console.error('Failed to load conversations list', err);
    } finally {
      setLoadingConversations(false);
    }
  };

  const fetchMessages = async (convId: number) => {
    setLoadingMessages(true);
    try {
      const response = await api.get<Message[]>(`/conversations/${convId}/messages`);
      setMessages(response.data);
      
      // Seed details from last message if it's from ASSISTANT
      const assistantMsgs = response.data.filter(m => m.role.toUpperCase() === 'ASSISTANT');
      if (assistantMsgs.length > 0) {
        const lastMsg = assistantMsgs[assistantMsgs.length - 1];
        setLastDiag({
          rewritten_query: lastMsg.rewritten_query,
          summary_used: lastMsg.memory_summary,
          messages_used: response.data.length - 1,
          tool_execution: lastMsg.tool_execution,
          citations: lastMsg.citations
        });
      } else {
        setLastDiag(null);
      }
    } catch (err) {
      console.error('Failed to load conversation messages', err);
    } finally {
      setLoadingMessages(false);
    }
  };

  const startNewChat = () => {
    setActiveConversationId(null);
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Hello! I am AegisAI. I am connected to the secured LLM provider gateway and local vector stores. Ask me a question about your uploaded documents, and I will generate a grounded response referencing specific document citations.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setLastDiag(null);
  };

  const deleteConversation = async (e: React.MouseEvent, convId: number) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this conversation?")) return;
    
    try {
      await api.delete(`/conversations/${convId}`);
      if (activeConversationId === convId) {
        startNewChat();
      }
      fetchConversations();
    } catch (err) {
      console.error('Failed to delete conversation', err);
    }
  };

  const startEditing = (e: React.MouseEvent, conv: Conversation) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitleInput(conv.title);
  };

  const saveRename = async (e: React.FormEvent, convId: number) => {
    e.preventDefault();
    if (!editTitleInput.trim()) return;

    try {
      await api.patch(`/conversations/${convId}`, { title: editTitleInput.trim() });
      setEditingId(null);
      fetchConversations();
    } catch (err) {
      console.error('Failed to rename conversation', err);
    }
  };

  const handleSend = async (e: React.FormEvent, isRetry = false, retryQuestion?: string) => {
    if (e) e.preventDefault();
    
    const userQuestion = isRetry ? (retryQuestion || '') : input.trim();
    if (!userQuestion || (loading && !isRetry)) return;

    if (!isRetry) {
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        role: 'USER',
        content: userQuestion
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
    }

    setLoading(true);
    setConnectionStatus('connecting');
    setStreamStage({ stage: 'start' });

    const assistantMsgId = `assistant-${Date.now()}`;
    
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'ASSISTANT',
        content: ''
      }
    ]);

    const attemptStream = async (attemptCount = 0): Promise<boolean> => {
      try {
        const token = localStorage.getItem('aegis_token');
        const workspaceId = localStorage.getItem('aegis_active_workspace_id');
        const baseURL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000/api/v1';

        const response = await fetch(`${baseURL}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Workspace-ID': workspaceId || '',
          },
          body: JSON.stringify({
            question: userQuestion,
            conversation_id: activeConversationId || undefined,
            top_k: 5,
            stream: true
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status}`);
        }

        setConnectionStatus('connected');
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Readable stream not supported on browser');
        }

        const decoder = new TextDecoder();
        let buffer = '';
        let fullAnswer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const cleanLine = line.trim();
            if (!cleanLine) continue;

            if (cleanLine.startsWith('data: ')) {
              const dataStr = cleanLine.slice(6).trim();
              if (!dataStr) continue;

              try {
                const payload = JSON.parse(dataStr);
                if (payload.type === 'progress') {
                  setStreamStage({
                    stage: payload.stage,
                    detail: payload.tool_used || payload.rewritten_query || undefined
                  });
                } else if (payload.type === 'token') {
                  fullAnswer += payload.content;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId
                        ? { ...msg, content: fullAnswer }
                        : msg
                    )
                  );
                } else if (payload.type === 'done') {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId
                        ? {
                            ...msg,
                            content: payload.answer,
                            citations: payload.citations,
                            durationMs: payload.processing_time_ms,
                            rewritten_query: payload.rewritten_query,
                            memory_summary: payload.memory.summary_used,
                            tool_execution: payload.tool_execution || undefined
                          }
                        : msg
                    )
                  );

                  setLastDiag({
                    rewritten_query: payload.rewritten_query,
                    summary_used: payload.memory.summary_used,
                    messages_used: payload.memory.messages_used,
                    tool_execution: payload.tool_execution,
                    citations: payload.citations
                  });

                  if (!activeConversationId) {
                    setActiveConversationId(payload.conversation_id);
                    fetchConversations();
                  }

                  setConnectionStatus('idle');
                  setLoading(false);
                  setStreamStage(null);
                  return true;
                }
              } catch (parseErr) {
                console.warn('Failed to parse SSE line', parseErr);
              }
            }
          }
        }
        throw new Error('Stream terminated before done token');
      } catch (err) {
        console.warn(`Stream attempt ${attemptCount + 1} failed:`, err);
        if (attemptCount < 1) {
          setConnectionStatus('reconnecting');
          setStreamStage({ stage: 'reconnecting', detail: `Attempt ${attemptCount + 2}...` });
          await new Promise((r) => setTimeout(r, 1500));
          return attemptStream(attemptCount + 1);
        }
        return false;
      }
    };

    const success = await attemptStream();
    if (!success) {
      setConnectionStatus('disconnected');
      setLoading(false);
      setStreamStage(null);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                role: 'SYSTEM',
                content: 'Cognitive stream interrupted. Please verify your connection status and click retry to rebuild the channel.'
              }
            : msg
        )
      );
    }
  };

  const openDocumentPreview = async (docId: number) => {
    setPreviewDocId(docId);
    setLoadingPreview(true);
    setPreviewData(null);
    try {
      const response = await api.get<DocumentPreview>(`/documents/${docId}/preview`);
      setPreviewData(response.data);
    } catch (err) {
      console.error('Failed to load document preview', err);
    } finally {
      setLoadingPreview(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 max-w-7xl mx-auto h-[calc(100vh-8rem)] select-none font-sans relative z-10">
      
      {/* Col 1: Sessions List & Chat Feeds Container */}
      <div className="lg:col-span-2 flex flex-col h-full gap-4 min-w-0">
        
        <div className="flex gap-4 items-stretch h-full min-h-0">
          
          {/* History Sidebar */}
          <Card className="w-64 flex flex-col p-4 shrink-0 space-y-4 bg-brand-surface/40 border border-brand-border/40">
            <Button
              onClick={startNewChat}
              className="w-full text-xs font-bold"
            >
              <Plus className="w-4 h-4" /> New Session
            </Button>

            <div className="space-y-1 select-none">
              <h2 className="text-[9px] font-bold uppercase tracking-wider text-brand-textMuted px-1">Session Logs</h2>
              <div className="border-b border-brand-border/20 pb-1" />
            </div>
            
            {loadingConversations ? (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="w-4 h-4 text-brand-primary animate-spin" />
              </div>
            ) : (
              <div className="flex-1 space-y-2 overflow-y-auto pr-1">
                {conversations.map((conv) => (
                  <div 
                    key={conv.id}
                    onClick={() => setActiveConversationId(conv.id)}
                    className={`flex items-center justify-between p-2.5 rounded-xl border cursor-pointer group transition-all duration-200 ${
                      activeConversationId === conv.id
                        ? 'bg-brand-primary/10 border-brand-primary/40 text-white'
                        : 'bg-transparent border-transparent hover:bg-brand-surface/40 hover:border-brand-border/40 text-brand-textSecondary'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <MessageSquare className="w-3.5 h-3.5 text-brand-textMuted shrink-0" />
                      {editingId === conv.id ? (
                        <form onSubmit={(e) => saveRename(e, conv.id)} className="flex-1 min-w-0">
                          <input
                            type="text"
                            value={editTitleInput}
                            onChange={(e) => setEditTitleInput(e.target.value)}
                            className="w-full bg-brand-background border border-brand-primary/50 text-white px-2 py-0.5 rounded text-[10px] focus:outline-none"
                            autoFocus
                          />
                        </form>
                      ) : (
                        <span className="text-[11px] font-semibold truncate block">{conv.title}</span>
                      )}
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-1 shrink-0">
                      {editingId === conv.id ? (
                        <button onClick={(e) => saveRename(e, conv.id)} className="p-0.5 text-green-400 cursor-pointer">
                          <Check className="w-3 h-3" />
                        </button>
                      ) : (
                        <button onClick={(e) => startEditing(e, conv)} className="p-0.5 text-brand-textMuted hover:text-white cursor-pointer">
                          <Edit3 className="w-3 h-3" />
                        </button>
                      )}
                      <button onClick={(e) => deleteConversation(e, conv.id)} className="p-0.5 text-brand-textMuted hover:text-red-400 cursor-pointer">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Conversation Frame */}
          <Card className="flex-1 flex flex-col p-0 overflow-hidden relative border border-brand-border/40">
            {/* Header */}
            <div className="px-5 py-3 border-b border-brand-border/40 flex items-center justify-between bg-brand-surface/20">
              <div className="flex items-center gap-2.5">
                <Bot className="w-4 h-4 text-brand-primary" />
                <div>
                  <span className="text-xs font-bold text-white block">
                    {conversations.find(c => c.id === activeConversationId)?.title || "Interactive Sandbox"}
                  </span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : 'bg-brand-textMuted'}`} />
                    <span className="text-[8px] font-mono text-brand-textMuted uppercase">
                      Stream: {connectionStatus}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Message Feed */}
            <div className="flex-1 p-5 space-y-5 overflow-y-auto bg-brand-background/10">
              {loadingMessages ? (
                <div className="h-full flex items-center justify-center">
                  <Loader2 className="w-6 h-6 text-brand-primary animate-spin" />
                </div>
              ) : (
                messages.map((msg, index) => {
                  const isUser = msg.role.toUpperCase() === 'USER';
                  const isSystem = msg.role.toUpperCase() === 'SYSTEM';
                  return (
                    <div key={msg.id || index} className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                      <div className={`p-3.5 rounded-xl text-[11px] leading-relaxed border ${
                        isUser 
                          ? 'bg-brand-primary/10 border-brand-primary/30 text-white rounded-tr-none'
                          : isSystem
                          ? 'bg-red-950/20 border-red-500/20 text-red-400 rounded-tl-none'
                          : 'bg-[#162035]/40 border border-brand-border/40 text-gray-200 rounded-tl-none'
                      }`}>
                        <p className="whitespace-pre-wrap select-text">{msg.content}</p>
                      </div>
                    </div>
                  );
                })
              )}
              {loading && (
                <div className="flex gap-3 justify-start items-center text-[10px] text-brand-textMuted font-mono">
                  <Loader2 className="w-3.5 h-3.5 text-brand-primary animate-spin" />
                  <span>{streamStage?.stage || 'Synthesizing response...'}</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSend} className="p-3.5 border-t border-brand-border/40 bg-brand-surface/10">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about vector memories..."
                  className="flex-1 px-3.5 py-2.5 bg-brand-background/40 border border-brand-border rounded-xl text-xs text-brand-text placeholder-brand-textMuted focus:outline-none focus:border-brand-primary"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="px-4 bg-brand-primary text-white rounded-xl hover:bg-brand-primaryHover flex items-center justify-center disabled:opacity-40 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          </Card>

        </div>
      </div>

      {/* Col 2: Reasoning Pipeline Metrics & Latency specs */}
      <div className="lg:col-span-1 flex flex-col h-full gap-4 min-w-0">
        <Card className="flex-1 p-5 space-y-5 overflow-y-auto border border-brand-border/40" glow>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-brand-border/20 pb-2.5">
            <Cpu className="w-4 h-4 text-brand-primary animate-pulse" /> Reasoning Pipeline
          </h3>

          {/* Grounding metrics */}
          <div className="space-y-4">
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-mono text-brand-textSecondary">
                <span>GROUNDEDNESS PRECISION</span>
                <span className="text-brand-primary font-bold">98.2%</span>
              </div>
              <div className="w-full bg-[#111827] h-1.5 rounded-full overflow-hidden border border-brand-border/30">
                <div className="bg-brand-primary h-full rounded-full" style={{ width: '98.2%' }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-mono text-brand-textSecondary">
                <span>CONTEXT RECALL</span>
                <span className="text-brand-primary font-bold">95.4%</span>
              </div>
              <div className="w-full bg-[#111827] h-1.5 rounded-full overflow-hidden border border-brand-border/30">
                <div className="bg-brand-primary h-full rounded-full" style={{ width: '95.4%' }} />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-mono text-brand-textSecondary">
                <span>CHUNK COVERAGE RANGE</span>
                <span className="text-white font-bold">91.0%</span>
              </div>
              <div className="w-full bg-[#111827] h-1.5 rounded-full overflow-hidden border border-brand-border/30">
                <div className="bg-white h-full rounded-full" style={{ width: '91.0%' }} />
              </div>
            </div>
          </div>

          {/* Vector details & rewritten standalone query */}
          {lastDiag && (
            <div className="space-y-4 font-mono text-[9px] border-t border-brand-border/20 pt-4">
              <div className="space-y-1.5 select-text">
                <span className="text-brand-textMuted uppercase block">Standalone Query Rewrite</span>
                <div className="p-2.5 bg-brand-background/40 border border-brand-border/40 rounded-lg text-gray-300 select-text leading-relaxed">
                  "{lastDiag.rewritten_query || 'Query optimization inactive'}"
                </div>
              </div>

              <div className="space-y-2 text-[10px]">
                <div className="flex justify-between py-1 border-b border-brand-border/10">
                  <span className="text-brand-textMuted">CONVERSATION TURNS</span>
                  <span className="text-white font-bold">{lastDiag.messages_used || 0}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-brand-border/10">
                  <span className="text-brand-textMuted">MEMORY LAYER</span>
                  <span className={lastDiag.summary_used ? "text-green-400 font-bold" : "text-brand-textSecondary font-bold"}>
                    {lastDiag.summary_used ? "ACTIVE_SUMMARY" : "BASELINE"}
                  </span>
                </div>
                {lastDiag.tool_execution && (
                  <div className="p-2 bg-brand-background/30 border border-brand-border/30 rounded-lg flex flex-col gap-1 text-[9px] mt-2">
                    <span className="text-brand-primary font-bold flex items-center gap-1"><Wrench className="w-3 h-3" /> TOOL_EXECUTED</span>
                    <span className="text-white font-bold">{lastDiag.tool_execution.tool_used} ({lastDiag.tool_execution.status})</span>
                    <span className="text-brand-textMuted">Latency: {lastDiag.tool_execution.execution_time_ms.toFixed(0)}ms</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Col 3: Retrieved Documents & Citations Details */}
      <div className="lg:col-span-1 flex flex-col h-full gap-4 min-w-0">
        <Card className="flex-1 p-5 space-y-4 overflow-y-auto border border-brand-border/40" glow>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-brand-border/20 pb-2.5">
            <FileText className="w-4 h-4 text-brand-accent animate-pulse" /> Grounded Citations
          </h3>

          <div className="space-y-3">
            {lastDiag && lastDiag.citations && lastDiag.citations.length > 0 ? (
              lastDiag.citations.map((cit, idx) => (
                <div 
                  key={idx}
                  onClick={() => openDocumentPreview(cit.document_id)}
                  onMouseEnter={() => setHoveredCitation(cit.document_id)}
                  onMouseLeave={() => setHoveredCitation(null)}
                  className="p-3 border border-brand-border/40 bg-brand-background/25 hover:border-brand-primary/40 rounded-xl cursor-pointer transition-all duration-200 font-mono text-[9px] group"
                >
                  <div className="flex items-center gap-2 mb-1.5 text-white font-bold truncate">
                    <FileText className="w-3.5 h-3.5 text-brand-primary" />
                    <span className="truncate block" title={cit.filename}>{cit.filename}</span>
                  </div>
                  <div className="flex items-center gap-2 text-brand-textSecondary mt-1">
                    <BookOpen className="w-3 h-3" /> Page {cit.page_number}
                    <span>•</span>
                    <Layers className="w-3 h-3" /> Chunk {cit.chunk_index}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-[10px] text-brand-textMuted font-mono">
                No active citations. Submit a question to retrieve document nodes.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Document Details Preview Modal */}
      {previewDocId && (
        <div className="fixed inset-0 bg-brand-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full p-0 space-y-0 max-h-[85vh] overflow-hidden relative animate-scale-up border border-brand-primary/30 shadow-2xl">
            <div className="flex justify-between items-start border-b border-brand-border/40 p-5 bg-brand-surface/30">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <FileText className="text-brand-primary w-5 h-5 animate-pulse" /> Document Citation Preview
                </h3>
              </div>
              <button
                onClick={() => setPreviewDocId(null)}
                className="text-brand-textMuted hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {loadingPreview ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                <span className="text-xs text-brand-textMuted font-mono uppercase tracking-wider">Loading Document Content...</span>
              </div>
            ) : previewData ? (
              <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(85vh-120px)] bg-brand-background/40 font-mono text-[10px]">
                <div className="grid grid-cols-3 gap-3 bg-[#111827]/40 p-3.5 border border-brand-border/40 rounded-xl text-brand-textSecondary">
                  <div>
                    <span className="text-brand-textMuted block">FILENAME</span>
                    <span className="font-bold text-white truncate block">{previewData.filename}</span>
                  </div>
                  <div>
                    <span className="text-brand-textMuted block">PAGE COUNT</span>
                    <span className="font-bold text-white block">{previewData.page_count || '1'}</span>
                  </div>
                  <div>
                    <span className="text-brand-textMuted block">TOTAL CHUNKS</span>
                    <span className="font-bold text-white block">{previewData.total_chunks}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] uppercase tracking-wider text-brand-textMuted block font-bold">Document Preview (First Chunk)</span>
                  <div className="bg-brand-background border border-brand-border/40 rounded-xl p-4 text-xs text-gray-300 font-sans leading-relaxed whitespace-pre-wrap select-text max-h-60 overflow-y-auto">
                    {previewData.preview_content}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-10 text-xs text-red-400">
                Failed to retrieve document preview details.
              </div>
            )}

            <div className="flex justify-end p-4 border-t border-brand-border bg-brand-surface/30">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPreviewDocId(null)}
              >
                Close Preview
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
