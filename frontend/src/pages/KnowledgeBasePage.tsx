import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';
import { 
  Database, Upload, CheckCircle2, AlertCircle, 
  Trash2, Loader2, FileText, RefreshCw, Clock, Eye 
} from 'lucide-react';

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
}

export const KnowledgeBasePage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-800 text-gray-400 border border-gray-700">
            <Clock className="w-3 h-3" /> Uploaded
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-yellow-950/40 text-yellow-500 border border-yellow-800/30">
            <Clock className="w-3 h-3 animate-pulse" /> Queued
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-950/50 text-blue-400 border border-blue-800/40">
            <Loader2 className="w-3 h-3 animate-spin" /> Processing
          </span>
        );
      case 'PROCESSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-green-950/50 text-green-400 border border-green-800/40">
            <CheckCircle2 className="w-3 h-3" /> Ready
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-950/50 text-red-400 border border-red-800/40">
            <AlertCircle className="w-3 h-3" /> Failed
          </span>
        );
    }
  };

  const renderVectorIndexStatus = (doc: Document) => {
    if (doc.status !== 'PROCESSED') {
      return <span className="text-gray-500 font-mono text-xs">-</span>;
    }
    
    const emb = embeddingStatuses[doc.id];
    if (!emb) {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] text-gray-500 font-mono">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-primary" /> Loading...
        </span>
      );
    }
    
    switch (emb.status) {
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase font-semibold font-mono bg-gray-900 text-gray-400 border border-gray-800">
            Pending
          </span>
        );
      case 'PROCESSING':
        const pct = emb.total_chunks > 0 ? Math.round((emb.indexed_chunks / emb.total_chunks) * 100) : 0;
        return (
          <div className="space-y-1 min-w-[100px]">
            <div className="flex justify-between text-[10px] font-mono text-blue-400">
              <span className="flex items-center gap-1"><Loader2 className="w-2.5 h-2.5 animate-spin" /> Indexing</span>
              <span>{pct}%</span>
            </div>
            <div className="w-full bg-brand-background rounded-full h-1 overflow-hidden border border-brand-border/40">
              <div className="bg-blue-500 h-1 rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      case 'INDEXED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase font-semibold font-mono bg-green-950/40 text-green-400 border border-green-800/30">
            {emb.indexed_chunks}/{emb.total_chunks} Ready
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] uppercase font-semibold font-mono bg-red-950/40 text-red-400 border border-red-800/30">
            Failed ({emb.failed_chunks} err)
          </span>
        );
      default:
        return <span className="text-gray-500 font-mono text-xs">-</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
            <p className="text-sm text-gray-400">Ingest, view, and manage corporate document assets securely.</p>
          </div>
        </div>
        <button 
          onClick={() => fetchDocuments(true)} 
          disabled={loadingList}
          className="btn-secondary px-3.5 py-2 flex items-center gap-1.5 text-xs focus:outline-none"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingList ? 'animate-spin' : ''}`} /> Sync List
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Panel */}
        <div className="lg:col-span-1 glass-card self-start">
          <h2 className="text-base font-semibold text-white mb-4">Ingest Document</h2>
          
          {error && (
            <div className="mb-4 p-4 rounded-lg bg-red-950/40 border border-red-800/40 text-red-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 rounded-lg bg-green-950/40 border border-green-800/40 text-green-300 text-xs flex items-start gap-2.5">
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
              className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all relative ${
                dragActive 
                  ? 'border-brand-primary bg-brand-primary/5' 
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
              <Upload className="w-8 h-8 text-gray-400 mb-2.5" />
              {file ? (
                <div className="text-center truncate w-full px-2">
                  <span className="text-xs font-semibold text-white block truncate">{file.name}</span>
                  <span className="text-[10px] text-gray-400">{formatSize(file.size)}</span>
                </div>
              ) : (
                <div className="text-center">
                  <span className="text-xs font-medium text-brand-text block">Click or Drag document here</span>
                  <span className="text-[10px] text-gray-500 mt-1 block">PDF, DOCX, or TXT up to 25MB</span>
                </div>
              )}
            </div>

            {uploading && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] text-gray-400">
                  <span>Uploading to gateway...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-brand-background rounded-full h-1.5 overflow-hidden">
                  <div 
                    className="bg-brand-primary h-1.5 rounded-full transition-all duration-100" 
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={uploading || !file}
              className="btn-primary w-full disabled:opacity-50 text-xs"
            >
              {uploading ? 'Processing File Ingestion...' : 'Upload & Process'}
            </button>
          </form>
        </div>

        {/* Documents Table */}
        <div className="lg:col-span-2 glass-card">
          <h2 className="text-base font-semibold text-white mb-4">Document Repository</h2>

          {loadingList ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
              <span className="text-xs text-gray-400 font-mono uppercase tracking-wider">Hydrating repository list...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-16 border border-brand-border/40 border-dashed rounded-xl bg-brand-background/5">
              <FileText className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <span className="text-sm font-semibold text-white block">No documents uploaded yet</span>
              <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                Ingest your first TXT, PDF, or DOCX document using the panel to trigger active vector index pipelines.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-brand-border text-[11px] uppercase tracking-wider text-gray-400 font-mono bg-brand-background/20">
                    <th className="py-3 px-4 font-semibold">Filename</th>
                    <th className="py-3 px-4 font-semibold">Type</th>
                    <th className="py-3 px-4 font-semibold">Size</th>
                    <th className="py-3 px-4 font-semibold">Chunks</th>
                    <th className="py-3 px-4 font-semibold">Vector Index</th>
                    <th className="py-3 px-4 font-semibold">Status</th>
                    <th className="py-3 px-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/40 text-sm">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-brand-surface/20 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-white truncate max-w-xs" title={doc.original_filename}>
                        {doc.original_filename}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-xs uppercase bg-brand-background px-1.5 py-0.5 rounded text-gray-300 border border-brand-border/40">
                          {doc.file_extension}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-gray-300 font-mono text-xs">
                        {formatSize(doc.file_size)}
                      </td>
                      <td className="py-3.5 px-4 text-gray-300 font-mono text-xs">
                        {doc.status === 'PROCESSED' ? doc.chunks_count : '-'}
                      </td>
                      <td className="py-3.5 px-4">
                        {renderVectorIndexStatus(doc)}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(doc.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        {doc.status === 'PROCESSED' && (
                          <button
                            onClick={() => handlePreview(doc.id)}
                            className="text-gray-400 hover:text-brand-primary p-1.5 rounded-lg hover:bg-brand-primary/10 transition-colors inline-flex"
                            title="Preview Extracted Text"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(doc.id, doc.original_filename)}
                          className="text-gray-400 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-950/20 transition-colors inline-flex"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Document Preview Modal */}
      {previewDocId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="glass-card w-full max-w-2xl flex flex-col max-h-[85vh] overflow-hidden border border-brand-border shadow-2xl relative animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-brand-border flex items-center justify-between bg-brand-surface/30">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-brand-primary" />
                <div>
                  <h3 className="text-base font-bold text-white">Document Preview</h3>
                  <p className="text-xs text-gray-400 font-mono mt-0.5 truncate max-w-md">
                    {previewData?.filename || 'Loading file details...'}
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setPreviewDocId(null)}
                className="text-gray-400 hover:text-white p-1 hover:bg-brand-surface rounded-lg transition-colors text-xs font-mono"
              >
                CLOSE
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-5 flex-1 bg-brand-background/40">
              {loadingPreview ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
                  <span className="text-xs text-gray-400 font-mono uppercase tracking-wider">Retrieving text segments...</span>
                </div>
              ) : previewError ? (
                <div className="p-4 rounded-xl border border-red-800/40 bg-red-950/20 text-red-400 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{previewError}</span>
                </div>
              ) : previewData ? (
                <div className="space-y-4">
                  {/* Stats Bar */}
                  <div className="grid grid-cols-3 gap-4 p-3.5 bg-brand-surface/40 border border-brand-border/40 rounded-xl font-mono text-xs">
                    <div className="text-center">
                      <span className="text-gray-400 block text-[10px] uppercase tracking-wider mb-0.5">Format</span>
                      <span className="text-white font-semibold">
                        {previewData.filename.split('.').pop()?.toUpperCase() || '-'}
                      </span>
                    </div>
                    <div className="text-center border-x border-brand-border/40">
                      <span className="text-gray-400 block text-[10px] uppercase tracking-wider mb-0.5">Pages</span>
                      <span className="text-white font-semibold">{previewData.page_count ?? 1}</span>
                    </div>
                    <div className="text-center">
                      <span className="text-gray-400 block text-[10px] uppercase tracking-wider mb-0.5">Total Chunks</span>
                      <span className="text-white font-semibold">{previewData.total_chunks}</span>
                    </div>
                  </div>
                  
                  {/* Extracted Text Box */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-gray-300 block uppercase tracking-wider">Preview Content (First Chunk snippet)</span>
                    <div className="p-4 rounded-xl border border-brand-border bg-brand-background font-mono text-xs text-gray-300 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto select-text scrollbar-thin">
                      {previewData.preview_content}
                    </div>
                    <span className="text-[10px] text-gray-500 block">
                      * Text contents above reflect the cleaned text segment stored in the primary chunk container. Chunking size: 1000 chars, Overlap: 200 chars.
                    </span>
                  </div>
                </div>
              ) : null}
            </div>
            
            {/* Modal Footer */}
            <div className="p-4 border-t border-brand-border bg-brand-surface/30 flex justify-end">
              <button 
                onClick={() => setPreviewDocId(null)}
                className="btn-secondary px-5 py-2 text-xs"
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
export type password = string;
