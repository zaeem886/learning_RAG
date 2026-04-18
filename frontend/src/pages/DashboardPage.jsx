import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiListDocuments, apiUploadDocument, apiDeleteDocument } from '../api/client';
import FileUpload from '../components/FileUpload';
import './DashboardPage.css';

export default function DashboardPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchDocs = useCallback(async () => {
    try {
      const docs = await apiListDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDocs(); }, [fetchDocs]);

  // Poll for processing documents
  useEffect(() => {
    const hasProcessing = documents.some(d => d.status === 'processing' || d.status === 'uploading');
    if (!hasProcessing) return;
    const timer = setInterval(fetchDocs, 3000);
    return () => clearInterval(timer);
  }, [documents, fetchDocs]);

  async function handleUpload(file) {
    setUploading(true);
    setError('');
    try {
      await apiUploadDocument(file);
      await fetchDocs();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this document and all its data?')) return;
    try {
      await apiDeleteDocument(id);
      setDocuments(prev => prev.filter(d => d.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  function statusBadge(status) {
    return <span className={`badge badge-${status}`}>{status}</span>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Your Documents</h1>
        <p>Upload PDFs and start chatting with AI-powered insights</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <FileUpload onUpload={handleUpload} uploading={uploading} />

      <div className="doc-grid">
        {loading ? (
          <div className="empty-state"><div className="spinner spinner-lg" /></div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <h3>No documents yet</h3>
            <p>Upload your first PDF to get started</p>
          </div>
        ) : (
          documents.map((doc, i) => (
            <div className="doc-card card fade-in" key={doc.id} style={{ animationDelay: `${i * 0.05}s` }}>
              <div className="doc-card-top">
                <div className="doc-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <line x1="10" y1="9" x2="8" y2="9"/>
                  </svg>
                </div>
                <div className="doc-info">
                  <h3 className="doc-name" title={doc.original_name}>{doc.original_name}</h3>
                  <div className="doc-meta">
                    {statusBadge(doc.status)}
                    {doc.chunk_count > 0 && (
                      <span className="doc-chunks">{doc.chunk_count} chunks</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="doc-card-bottom">
                <span className="doc-date">
                  {new Date(doc.upload_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
                <div className="doc-actions">
                  {doc.status === 'ready' && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => navigate(`/chat?doc=${doc.id}`)}
                      id={`chat-doc-${doc.id}`}
                    >
                      Chat
                    </button>
                  )}
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(doc.id)}
                    id={`delete-doc-${doc.id}`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
