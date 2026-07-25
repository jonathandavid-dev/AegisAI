import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';
import { 
  Database, Upload, CheckCircle2, AlertCircle, 
  Trash2, Loader2, FileText, RefreshCw, Clock, Eye 
} from 'lucide-react';
import { Card, Button, Input, Progress, Skeleton, EmptyState, Badge } from '../components/ui/Primitives';
import { useKnowledgeUniverse } from '../context/KnowledgeUniverseContext';

interface Document {
  id: number;
  account_id: number;
  original_filename: string;
  stored_filename: string;
  file_extension: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  status: 'UPLOADED' | 'QUEUED' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
  created_at: string;
  updated_at: string;
  chunks_count?: number;
}

export const KnowledgeBasePage: React.FC = () => {
  const { triggerIngestSequence } = useKnowledgeUniverse();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const pollIntervalRef = useRef<any | null>(null);

  // Preview Modal state
  const [previewDocId, setPreviewDocId] = useState<number | null>(null);
  const [previewData, setPreviewData] = useState<{
    filename: string;
    page_count: number | null;
    total_chunks: number;
    preview_content: string;
  } | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // Embedding Status state
  const [embeddingStatuses, setEmbeddingStatuses] = useState<Record<number, {
    document_id: number;
    status: string;
    total_chunks: number;
    indexed_chunks: number;
    failed_chunks: number;
  }>>({});

  // 1. Fetch document list
  const fetchDocuments = useCallback(async (showLoading = false) => {
    if (showLoading) setLoadingList(true);
    try {
      const response = await api.get<Document[]>('/documents');
      setDocuments(response.data);
    } catch (err: any) {
      console.error("Failed to load documents list", err);
      setError("Unable to retrieve documents list");
    } finally {
      if (showLoading) setLoadingList(false);
    }
  }, []);

  // 2. Set up polling for active background processing statuses
  useEffect(() => {
    fetchDocuments(true);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [fetchDocuments]);

  // Monitor list: if any document is in UPLOADED/QUEUED/PROCESSING, OR its embedding status is not INDEXED/FAILED, poll status!
  useEffect(() => {
    const hasActiveTasks = documents.some(
      doc => doc.status === 'UPLOADED' || doc.status === 'QUEUED' || doc.status === 'PROCESSING'
    );
    
    const hasActiveEmbeddings = documents.some(doc => {
      if (doc.status !== 'PROCESSED') return false;
      const emb = embeddingStatuses[doc.id];
      return !emb || emb.status === 'PENDING' || emb.status === 'PROCESSING';
    });
 
    if (hasActiveTasks || hasActiveEmbeddings) {
      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(() => {
          fetchDocuments(false);
        }, 3000); // poll every 3s
      }
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [documents, embeddingStatuses, fetchDocuments]);

  // Fetch embedding statuses for processed documents
  useEffect(() => {
    const processedDocs = documents.filter(doc => doc.status === 'PROCESSED');
    processedDocs.forEach(async (doc) => {
      // Only fetch if not already loaded as INDEXED or FAILED, to prevent redundant API calls
      const current = embeddingStatuses[doc.id];
      if (current && (current.status === 'INDEXED' || current.status === 'FAILED')) {
        return;
      }
      try {
        const response = await api.get(`/documents/${doc.id}/embedding-status`);
        setEmbeddingStatuses(prev => ({
          ...prev,
          [doc.id]: response.data
        }));
      } catch (err) {
        console.error(`Failed to fetch embedding status for document ${doc.id}`, err);
      }
    });
  }, [documents]);

  // 3. Handlers for drag and drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    setSuccess(null);
    
    // Check extension
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    const allowed = ['pdf', 'docx', 'txt'];
    if (!ext || !allowed.includes(ext)) {
      setError(`File type not supported (.${ext}). Only PDF, DOCX, and TXT are accepted.`);
      setFile(null);
      return;
    }

    // Check size (reject empty and limit to 25MB by default)
    if (selectedFile.size === 0) {
      setError("Cannot upload empty files");
      setFile(null);
      return;
    }

    const maxSize = 25 * 1024 * 1024; // 25MB
    if (selectedFile.size > maxSize) {
      setError("File exceeds maximum allowed size of 25MB");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  // 4. File upload execution
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        }
      });
      setSuccess(`File "${file.name}" uploaded successfully. Celery pipeline started.`);
      triggerIngestSequence(file.name);
      setFile(null);
      await fetchDocuments(false);
      
      // Reset input element
      const fileInput = document.getElementById('kb-file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        "File upload failed. Ensure the database and workers are active."
      );
    } finally {
      setUploading(false);
    }
  };

  // 5. Delete document controller
  const handleDelete = async (id: number, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await api.delete(`/documents/${id}`);
      setSuccess(`Document "${filename}" deleted successfully.`);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    } catch (err: any) {
      setError("Failed to delete the document.");
    }
  };

  // 6. Preview document controller
  const handlePreview = async (docId: number) => {
    setPreviewDocId(docId);
    setLoadingPreview(true);
    setPreviewError(null);
    setPreviewData(null);
    try {
      const response = await api.get(`/documents/${docId}/preview`);
      setPreviewData(response.data);
    } catch (err: any) {
      console.error("Failed to load document preview", err);
      setPreviewError("Unable to retrieve document text preview");
    } finally {
      setLoadingPreview(false);
    }
  };

  // 6. Utility formatters
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusBadge = (status: Document['status']) => {
    switch (status) {
      case 'UPLOADED':
        return <Badge variant="secondary"><Clock className="w-3 h-3 inline mr-1" /> Uploaded</Badge>;
      case 'QUEUED':
        return <Badge variant="warning"><Clock className="w-3 h-3 inline mr-1 animate-pulse" /> Queued</Badge>;
      case 'PROCESSING':
        return <Badge variant="primary"><Loader2 className="w-3 h-3 inline mr-1 animate-spin" /> Processing</Badge>;
      case 'PROCESSED':
        return <Badge variant="success"><CheckCircle2 className="w-3 h-3 inline mr-1" /> Ready</Badge>;
      case 'FAILED':
        return <Badge variant="danger"><AlertCircle className="w-3 h-3 inline mr-1" /> Failed</Badge>;
    }
  };

  const renderVectorIndexStatus = (doc: Document) => {
    if (doc.status !== 'PROCESSED') {
      return <span className="text-brand-textMuted font-mono text-xs">-</span>;
    }
    
    const emb = embeddingStatuses[doc.id];
    if (!emb) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] text-brand-textMuted font-mono">
          <Loader2 className="w-3 h-3 animate-spin text-brand-primary" /> Loading...
        </span>
      );
    }
    
    switch (emb.status) {
      case 'PENDING':
        return <Badge variant="secondary">Pending</Badge>;
      case 'PROCESSING':
        const pct = emb.total_chunks > 0 ? Math.round((emb.indexed_chunks / emb.total_chunks) * 100) : 0;
        return (
          <div className="space-y-1 min-w-[100px]">
            <div className="flex justify-between text-[10px] font-mono text-brand-primary">
              <span className="flex items-center gap-1"><Loader2 className="w-2.5 h-2.5 animate-spin" /> Indexing</span>
              <span>{pct}%</span>
            </div>
            <Progress value={pct} />
          </div>
        );
      case 'INDEXED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase font-semibold font-mono bg-green-500/10 text-green-400 border border-green-500/20">
            {emb.indexed_chunks}/{emb.total_chunks} Indexed
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase font-semibold font-mono bg-red-500/10 text-red-400 border border-red-500/20">
            Failed ({emb.failed_chunks} err)
          </span>
        );
      default:
        return <span className="text-brand-textMuted font-mono text-xs">-</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto select-none animate-fade-in-up">
      {/* Header section */}
      <div className="flex items-center justify-between border-b border-brand-border/40 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary shadow-[0_0_15px_rgba(16,185,129,0.12)]">
            <Database className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white">Knowledge Library</h1>
            <p className="text-xs text-brand-textSecondary">Ingest, view, and manage corporate document assets securely.</p>
          </div>
        </div>
        <Button 
          variant="secondary" 
          size="sm"
          onClick={() => fetchDocuments(true)} 
          disabled={loadingList}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingList ? 'animate-spin' : ''}`} /> Sync Library
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Panel */}
        <Card className="lg:col-span-1 self-start p-6" glow>
          <h2 className="text-xs font-bold text-white uppercase tracking-wider mb-4 font-mono">Ingest Vector Core</h2>
          
          {error && (
            <div className="p-4 rounded-xl bg-red-950/20 border border-red-800/30 text-red-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-4 rounded-xl bg-green-950/20 border border-green-800/30 text-green-400 text-xs flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-green-400" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleUpload} className="space-y-4">
            <div 
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 relative ${
                dragActive 
                  ? 'border-brand-primary bg-brand-primary/10' 
                  : 'border-brand-border/60 hover:border-brand-primary/50 bg-brand-background/15'
              }`}
            >
              <input 
                id="kb-file-input"
                type="file" 
                onChange={handleFileChange}
                accept=".pdf,.docx,.txt"
                className="absolute inset-0 opacity-0 cursor-pointer" 
              />
              <Upload className="w-8 h-8 text-brand-textMuted mb-2.5" />
              {file ? (
                <div className="text-center truncate w-full px-2">
                  <span className="text-xs font-bold text-white block truncate">{file.name}</span>
                  <span className="text-[10px] text-brand-textMuted font-mono">{formatSize(file.size)}</span>
                </div>
              ) : (
                <div className="text-center">
                  <span className="text-xs font-bold text-brand-text block">Click or Drag document here</span>
                  <span className="text-[9px] text-brand-textMuted mt-1 block">PDF, DOCX, or TXT up to 25MB</span>
                </div>
              )}
            </div>

            {uploading && (
              <div className="space-y-1.5 font-mono">
                <div className="flex justify-between text-[10px] text-brand-textMuted">
                  <span>Uploading to core...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
                
                {/* Volumetric green streaming upload indicator */}
                <div className="w-full flex items-center justify-center py-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-brand-primary animate-ping" />
                </div>
              </div>
            )}

            <Button
              type="submit"
              disabled={uploading || !file}
              className="w-full text-xs font-bold"
            >
              {uploading ? 'Processing File Ingestion...' : 'Upload & Process'}
            </Button>
          </form>
        </Card>

        {/* Documents Gallery Card List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center border-b border-brand-border/40 pb-2 mb-2 select-none">
            <h2 className="text-[10px] font-bold text-brand-textMuted uppercase tracking-wider font-mono">Document Repository</h2>
            <span className="text-[9px] text-brand-textMuted font-mono uppercase font-bold">{documents.length} Assets Ingested</span>
          </div>

          {loadingList ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-32 w-full" />
              ))}
            </div>
          ) : documents.length === 0 ? (
            <EmptyState
              title="No documents uploaded yet"
              description="Ingest your first TXT, PDF, or DOCX document using the panel to trigger active vector index pipelines."
              icon={FileText}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {documents.map((doc) => (
                <Card 
                  key={doc.id}
                  className="bg-brand-surface/40 hover:bg-brand-surface/80 border border-brand-border/40 hover:border-brand-primary/40 p-5 rounded-2xl flex flex-col justify-between h-40 transition-all duration-300 relative group overflow-hidden"
                  glow
                >
                  {/* Volumetric glow on hover */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-brand-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                  {/* Header Card details */}
                  <div className="flex justify-between items-start min-w-0">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className={`p-2 rounded-xl bg-brand-background border border-brand-border/40 shrink-0 ${
                        doc.file_extension === 'pdf' ? 'text-red-400' :
                        doc.file_extension === 'docx' ? 'text-blue-400' : 'text-brand-accent'
                      }`}>
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="truncate">
                        <span className="text-xs font-bold text-white block truncate" title={doc.original_filename}>
                          {doc.original_filename}
                        </span>
                        <span className="text-[9px] text-brand-textMuted font-mono uppercase tracking-wider block mt-0.5">
                          {doc.file_extension} • {formatSize(doc.file_size)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Status Indicator Details */}
                  <div className="space-y-2 py-2">
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className="text-brand-textMuted">PIPELINE:</span>
                      <span>{getStatusBadge(doc.status)}</span>
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className="text-brand-textMuted">VECTOR CORE:</span>
                      <span>{renderVectorIndexStatus(doc)}</span>
                    </div>
                  </div>

                  {/* Actions footer hover strip */}
                  <div className="border-t border-brand-border/40 pt-2 flex justify-between items-center relative z-10">
                    <span className="text-[8px] text-brand-textMuted font-mono uppercase tracking-wider">
                      Chunks: {doc.status === 'PROCESSED' ? (doc.chunks_count || '-') : '-'}
                    </span>
                    <div className="flex gap-2">
                      {doc.status === 'PROCESSED' && (
                        <button
                          onClick={() => handlePreview(doc.id)}
                          className="text-brand-textMuted hover:text-brand-primary p-1 rounded hover:bg-white/5 transition-colors cursor-pointer"
                          title="Preview Extracted Text"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        className="text-brand-textMuted hover:text-red-400 p-1 rounded hover:bg-white/5 transition-colors cursor-pointer"
                        title="Delete Document"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Document Preview Modal */}
      {previewDocId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-scale-up">
          <Card className="w-full max-w-2xl flex flex-col max-h-[85vh] overflow-hidden border border-brand-primary/30 p-0 shadow-2xl relative">
            {/* Modal Header */}
            <div className="p-5 border-b border-brand-border flex items-center justify-between bg-brand-surface/30">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-brand-primary animate-pulse" />
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Document Preview</h3>
                  <p className="text-[10px] text-brand-textMuted font-mono mt-0.5 truncate max-w-md">
                    {previewData?.filename || 'Loading file details...'}
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setPreviewDocId(null)}
                className="text-brand-textMuted hover:text-white p-1 hover:bg-brand-surface rounded-lg transition-colors text-xs font-mono cursor-pointer"
              >
                CLOSE
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-5 flex-1 bg-brand-background/40">
              {loadingPreview ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                  <span className="text-xs text-brand-textMuted font-mono uppercase tracking-wider">Retrieving text segments...</span>
                </div>
              ) : previewError ? (
                <div className="p-4 rounded-xl border border-red-800/40 bg-red-950/20 text-red-400 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{previewError}</span>
                </div>
              ) : previewData ? (
                <div className="space-y-4">
                  {/* Stats Bar */}
                  <div className="grid grid-cols-3 gap-4 p-3.5 bg-[#111827]/40 border border-brand-border/40 rounded-xl font-mono text-[10px]">
                    <div className="text-center">
                      <span className="text-brand-textMuted block uppercase tracking-wider mb-0.5">Format</span>
                      <span className="text-white font-bold">
                        {previewData.filename.split('.').pop()?.toUpperCase() || '-'}
                      </span>
                    </div>
                    <div className="text-center border-x border-brand-border/40">
                      <span className="text-brand-textMuted block uppercase tracking-wider mb-0.5">Pages</span>
                      <span className="text-white font-bold">{previewData.page_count ?? 1}</span>
                    </div>
                    <div className="text-center">
                      <span className="text-brand-textMuted block uppercase tracking-wider mb-0.5">Total Chunks</span>
                      <span className="text-white font-bold">{previewData.total_chunks}</span>
                    </div>
                  </div>
                  
                  {/* Extracted Text Box */}
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-gray-300 block uppercase tracking-wider">Preview Content (First Chunk snippet)</span>
                    <div className="p-4 rounded-xl border border-brand-border bg-brand-background font-mono text-[11px] text-gray-300 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto select-text scrollbar-thin">
                      {previewData.preview_content}
                    </div>
                    <span className="text-[9px] text-brand-textMuted block">
                      * Text contents above reflect the cleaned text segment stored in the primary chunk container. Chunking size: 1000 chars, Overlap: 200 chars.
                    </span>
                  </div>
                </div>
              ) : null}
            </div>
            
            {/* Modal Footer */}
            <div className="p-4 border-t border-brand-border bg-brand-surface/30 flex justify-end">
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
export type password = string;
