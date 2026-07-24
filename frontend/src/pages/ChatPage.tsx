import React, { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  User, 
  Loader2, 
  X, 
  FileText, 
  BookOpen, 
  Layers, 
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Edit3,
  Check,
  BrainCircuit,
  CornerDownRight,
  Wrench,
  Activity
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
}

interface ChatResponse {
  conversation_id: number;
  question: string;
  rewritten_query: string;
  answer: string;
  citations: Citation[];
  retrieval: {
    chunks_used: number;
  };
  memory: {
    summary_used: boolean;
    messages_used: number;
  };
  tool_execution: ToolExecution | null;
  processing_time_ms: number;
}

interface DocumentPreview {
  filename: string;
  page_count: number | null;
  total_chunks: number;
  preview_content: string;
}

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  
  // Phase 3.3 Streaming States
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'disconnected' | 'reconnecting'>('idle');
  const [streamStage, setStreamStage] = useState<{ stage: string; detail?: string } | null>(null);

  // Citations toggling state
  const [activeCitationsIdx, setActiveCitationsIdx] = useState<Record<string | number, boolean>>({});

  // Inline rename state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitleInput, setEditTitleInput] = useState('');

  // Diagnostic states for the last message
  const [lastDiag, setLastDiag] = useState<{
    rewritten_query?: string;
    summary_used?: boolean;
    messages_used?: number;
    tool_execution?: ToolExecution | null;
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
      setLastDiag(null);
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
        const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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
                    tool_execution: payload.tool_execution
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


  const toggleCitations = (msgId: string | number) => {
    setActiveCitationsIdx(prev => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
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
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      {/* Conversations Sidebar List */}
      <div className="w-80 glass-card flex flex-col p-4 shrink-0">
        <button
          onClick={startNewChat}
          className="w-full mb-4 px-4 py-2.5 bg-brand-primary text-white text-xs font-semibold uppercase tracking-wider rounded-xl hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" /> New Conversation
        </button>

        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-2 px-2">History Logs</h2>
        
        {loadingConversations ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-brand-primary animate-spin" />
          </div>
        ) : (
          <div className="flex-1 space-y-2 overflow-y-auto pr-1">
            {conversations.map((conv) => (
              <div 
                key={conv.id}
                onClick={() => setActiveConversationId(conv.id)}
                className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer group transition-all ${
                  activeConversationId === conv.id
                    ? 'bg-brand-primary/10 border-brand-primary/30 text-white'
                    : 'bg-brand-surface/20 border-transparent hover:bg-brand-surface/40 text-gray-400 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <MessageSquare className={`w-4 h-4 shrink-0 ${activeConversationId === conv.id ? 'text-brand-primary' : 'text-gray-400'}`} />
                  
                  {editingId === conv.id ? (
                    <form 
                      onSubmit={(e) => saveRename(e, conv.id)} 
                      onClick={(e) => e.stopPropagation()}
                      className="flex-1 min-w-0"
                    >
                      <input
                        type="text"
                        value={editTitleInput}
                        onChange={(e) => setEditTitleInput(e.target.value)}
                        className="w-full bg-brand-background border border-brand-primary/50 text-white px-2 py-0.5 rounded text-xs focus:outline-none"
                        autoFocus
                      />
                    </form>
                  ) : (
                    <span className="text-xs font-semibold truncate block">{conv.title}</span>
                  )}
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2 shrink-0">
                  {editingId === conv.id ? (
                    <button 
                      onClick={(e) => saveRename(e, conv.id)}
                      className="p-1 text-green-400 hover:bg-white/5 rounded"
                      title="Confirm Rename"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <button
                      onClick={(e) => startEditing(e, conv)}
                      className="p-1 text-gray-400 hover:text-white hover:bg-white/5 rounded"
                      title="Rename Session"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    onClick={(e) => deleteConversation(e, conv.id)}
                    className="p-1 text-gray-400 hover:text-red-400 hover:bg-white/5 rounded"
                    title="Delete Session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Main Conversation Window */}
      <div className="flex-1 glass-card flex flex-col p-0 overflow-hidden">
        {/* Chat Panel Header */}
        <div className="px-6 py-4 border-b border-brand-border/60 flex items-center justify-between bg-[#0E1322]">
          <div className="flex items-center gap-3">
            <Bot className="w-5 h-5 text-brand-primary animate-pulse" />
            <div>
              <span className="text-sm font-semibold text-white block">
                {conversations.find(c => c.id === activeConversationId)?.title || "AegisAI Multi-Turn Session"}
              </span>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="text-[10px] text-green-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-ping" /> Cognitive Memory Enabled
                </span>
                <span className={`text-[10px] flex items-center gap-1 font-mono uppercase tracking-wider ${
                  connectionStatus === 'connected' ? 'text-green-400' :
                  connectionStatus === 'connecting' || connectionStatus === 'reconnecting' ? 'text-yellow-400 animate-pulse' :
                  connectionStatus === 'disconnected' ? 'text-red-400 animate-pulse' : 'text-gray-500'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-green-400' :
                    connectionStatus === 'connecting' || connectionStatus === 'reconnecting' ? 'bg-yellow-400' :
                    connectionStatus === 'disconnected' ? 'bg-red-400' : 'bg-gray-500'
                  }`} />
                  Stream: {connectionStatus}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1.5 bg-brand-accent/10 border border-brand-accent/20 rounded-lg px-2.5 py-1 text-brand-accent text-xs font-mono uppercase tracking-wider">
            <BrainCircuit className="w-3.5 h-3.5 text-brand-primary animate-pulse" /> Layered Memory
          </div>
        </div>


        {/* Message Feed Container */}
        <div className="flex-1 p-6 space-y-6 overflow-y-auto bg-brand-background/5">
          {loadingMessages ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
            </div>
          ) : (
            messages.map((msg, index) => {
              const isAssistant = msg.role.toUpperCase() === 'ASSISTANT';
              const isUser = msg.role.toUpperCase() === 'USER';
              const isSystem = msg.role.toUpperCase() === 'SYSTEM';

              return (
                <div 
                  key={msg.id || index} 
                  className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {/* Avatar Icon */}
                  {!isUser && (
                    <div className="w-8 h-8 rounded-lg bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  {/* Message content bubble */}
                  <div className="max-w-[75%] space-y-2">
                    <div className={`p-4 rounded-2xl text-sm leading-relaxed border ${
                      isUser 
                        ? 'bg-gradient-to-r from-brand-primary to-brand-accent text-white border-transparent rounded-tr-none font-medium'
                        : isSystem
                        ? 'bg-red-950/20 border-red-500/20 text-red-400'
                        : 'bg-brand-surface border-brand-border/60 text-gray-300 rounded-tl-none'
                    }`}>
                      <p className="whitespace-pre-wrap select-text">{msg.content}</p>
                      
                      {isSystem && msg.content.includes("Cognitive stream") && (
                        <button
                          type="button"
                          onClick={() => {
                            const userMsgs = messages.filter(m => m.role.toUpperCase() === 'USER');
                            const lastQuestion = userMsgs.length > 0 ? userMsgs[userMsgs.length - 1].content : '';
                            setMessages(prev => prev.filter(m => m.id !== msg.id));
                            handleSend(null as any, true, lastQuestion);
                          }}
                          className="mt-2.5 px-3 py-1 bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold rounded-lg hover:bg-red-500/30 transition-all flex items-center gap-1"
                        >
                          <Activity className="w-3.5 h-3.5 animate-pulse" /> Reconnect & Retry Turn
                        </button>
                      )}

                      {/* Telemetry info */}
                      {isAssistant && msg.durationMs && (
                        <span className="text-[9px] text-gray-500 font-mono block mt-2 flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" /> Computed response in {msg.durationMs.toFixed(0)}ms
                        </span>
                      )}
                    </div>


                    {/* Tool Execution Badge (Dynamic Badge Display) */}
                    {isAssistant && msg.tool_execution && (
                      <div className="flex flex-wrap items-center gap-2 mt-1.5 p-2 bg-brand-surface/60 border border-brand-border/50 rounded-xl text-[10px] text-gray-400 font-mono">
                        <Wrench className="w-3.5 h-3.5 text-brand-primary" />
                        <span>Tool Used:</span>
                        <span className="text-white font-semibold">{msg.tool_execution.tool_used}</span>
                        <span className="text-gray-600">•</span>
                        <span>Duration:</span>
                        <span className="text-white font-semibold">{msg.tool_execution.execution_time_ms.toFixed(1)}ms</span>
                        <span className="text-gray-600">•</span>
                        <span>Status:</span>
                        <span className={msg.tool_execution.status === "success" ? "text-green-400 font-semibold" : "text-red-400 font-semibold"}>
                          {msg.tool_execution.status.toUpperCase()}
                        </span>
                      </div>
                    )}

                    {/* Expandable References / Citations */}
                    {isAssistant && msg.citations && msg.citations.length > 0 && (
                      <div className="space-y-1">
                        <button
                          onClick={() => toggleCitations(msg.id || index)}
                          className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400 font-mono hover:text-brand-primary transition-colors focus:outline-none"
                        >
                          {activeCitationsIdx[msg.id || index] ? (
                            <>Hide Citations <ChevronUp className="w-3.5 h-3.5" /></>
                          ) : (
                            <>Show Citations ({msg.citations.length}) <ChevronDown className="w-3.5 h-3.5" /></>
                          )}
                        </button>
                        
                        {activeCitationsIdx[msg.id || index] && (
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1.5 animate-fade-in">
                            {msg.citations.map((cit, idx) => (
                              <div 
                                key={idx}
                                onClick={() => openDocumentPreview(cit.document_id)}
                                className="p-2.5 border border-brand-border/50 rounded-xl bg-brand-background/40 hover:border-brand-primary/50 cursor-pointer transition-colors flex items-center gap-2.5 group"
                              >
                                <FileText className="w-4 h-4 text-brand-primary shrink-0 group-hover:scale-105 transition-transform" />
                                <div className="truncate font-mono text-[10px]">
                                  <span className="text-white font-semibold truncate block" title={cit.filename}>{cit.filename}</span>
                                  <span className="text-gray-400 flex items-center gap-1">
                                    <BookOpen className="w-3 h-3 text-gray-500" /> Page {cit.page_number} 
                                    <span className="text-gray-600">•</span>
                                    <Layers className="w-3 h-3 text-gray-500" /> Chunk {cit.chunk_index}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-lg bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center text-brand-accent shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {/* Streaming Loading Indicator */}
          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="w-8 h-8 rounded-lg bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary shrink-0">
                <Bot className="w-4 h-4 animate-bounce" />
              </div>
              <div className="bg-brand-surface border border-brand-border/60 p-4 rounded-2xl rounded-tl-none max-w-[70%] space-y-2">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 text-brand-primary animate-spin" />
                  <span className="text-xs text-gray-400 font-mono">
                    {streamStage?.stage === 'context_preparation' ? 'Rewriting standalone query...' :
                     streamStage?.stage === 'tool_execution' ? `Running tool: ${streamStage.detail || 'agent task'}...` :
                     streamStage?.stage === 'embedding' ? 'Encoding semantic vector query...' :
                     streamStage?.stage === 'retrieval' ? 'Retrieving grounded knowledge segments...' :
                     streamStage?.stage === 'llm_generation' ? 'Generating response...' :
                     streamStage?.stage === 'reconnecting' ? `Reconnecting stream: ${streamStage.detail || 'waiting'}` :
                     'Initializing cognitive stream connection...'}
                  </span>
                </div>
                <div className="flex gap-1.5 items-center py-1 px-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}


          <div ref={messagesEndRef} />
        </div>

        {/* Diagnostic Memory Telemetry panel */}
        {lastDiag && (
          <div className="px-6 py-3.5 border-t border-brand-border/40 bg-brand-surface/20 flex flex-col gap-2 text-[10px] text-gray-400 font-mono border-b border-brand-border/40">
            <div className="flex items-center gap-1.5">
              <CornerDownRight className="w-3.5 h-3.5 text-brand-primary" />
              <span>Standalone Query:</span>
              <span className="text-white font-semibold">"{lastDiag.rewritten_query}"</span>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
              <span className="flex items-center gap-1">
                <BrainCircuit className="w-3.5 h-3.5 text-brand-accent" /> Message Turns: <span className="text-white font-semibold">{lastDiag.messages_used}</span>
              </span>
              <span className="flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-brand-accent" /> Summary Layer: <span className={lastDiag.summary_used ? "text-green-400 font-semibold" : "text-gray-500 font-semibold"}>{lastDiag.summary_used ? "ACTIVE" : "INACTIVE"}</span>
              </span>
              {lastDiag.tool_execution && (
                <span className="flex items-center gap-1">
                  <Wrench className="w-3.5 h-3.5 text-brand-primary" /> Active Tool: <span className="text-white font-semibold">{lastDiag.tool_execution.tool_used} ({lastDiag.tool_execution.status})</span>
                </span>
              )}
            </div>
          </div>
        )}

        {/* Input box */}
        <form onSubmit={handleSend} className="p-4 border-t border-brand-border/60 bg-[#0E1322]">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question or enter a tool task (e.g. Calculate 18% of 14500)..."
              className="flex-1 px-4 py-3 bg-brand-background border border-brand-border/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary/80 focus:ring-1 focus:ring-brand-primary/50 transition-all font-sans text-sm"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-5 bg-gradient-to-r from-brand-primary to-brand-accent text-white font-medium rounded-xl hover:opacity-90 transition-opacity flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
              title="Send Message"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Document Details Preview Modal */}
      {previewDocId && (
        <div className="fixed inset-0 bg-brand-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto relative animate-scale-up border border-brand-primary/30">
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-brand-border/40 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <FileText className="text-brand-primary w-5 h-5" /> Document Citation Preview
                </h3>
              </div>
              <button
                onClick={() => setPreviewDocId(null)}
                className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingPreview ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                <span className="text-xs text-gray-400 font-mono uppercase tracking-wider">Loading Document Content...</span>
              </div>
            ) : previewData ? (
              <div className="space-y-4">
                {/* Document metadata table */}
                <div className="grid grid-cols-3 gap-3 bg-brand-background/40 p-3 border border-brand-border/40 rounded-xl font-mono text-xs text-gray-300">
                  <div>
                    <span className="text-[10px] text-gray-500 block">FILENAME</span>
                    <span className="font-semibold text-white truncate block">{previewData.filename}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-500 block">PAGE COUNT</span>
                    <span className="font-semibold text-white block">{previewData.page_count || '1'}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-500 block">TOTAL CHUNKS</span>
                    <span className="font-semibold text-white block">{previewData.total_chunks}</span>
                  </div>
                </div>

                {/* Chunk text content */}
                <div className="space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-gray-500 block">Document Preview (First Chunk)</span>
                  <div className="bg-brand-background border border-brand-border/40 rounded-xl p-4 max-h-[40vh] overflow-y-auto text-sm text-gray-300 font-sans leading-relaxed whitespace-pre-wrap select-text">
                    {previewData.preview_content}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-10 text-sm text-red-400">
                Failed to retrieve document preview details.
              </div>
            )}

            {/* Close footer */}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setPreviewDocId(null)}
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
