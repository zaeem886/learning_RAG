import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiAskQuestion, apiListDocuments, apiListSessions, apiGetSessionMessages } from '../api/client';
import ChatMessage from '../components/ChatMessage';
import './ChatPage.css';

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const docIdParam = searchParams.get('doc');

  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(docIdParam ? Number(docIdParam) : null);
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  // Load documents and sessions
  useEffect(() => {
    apiListDocuments().then(docs => {
      const readyDocs = docs.filter(d => d.status === 'ready');
      setDocuments(readyDocs);
    }).catch(() => {});

    apiListSessions().then(setSessions).catch(() => {});
  }, []);

  // Load session messages when active session changes
  useEffect(() => {
    if (!activeSession) return;
    apiGetSessionMessages(activeSession).then(msgs => {
      setMessages(msgs.map(m => ({
        role: m.role,
        content: m.content,
        sources: m.sources ? JSON.parse(m.sources) : [],
      })));
    }).catch(() => {});
  }, [activeSession]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const q = query.trim();
    setQuery('');
    setError('');

    // Optimistic UI: add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: q, sources: [] }]);
    setLoading(true);

    try {
      const res = await apiAskQuestion(q, selectedDoc, activeSession);
      setActiveSession(res.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: res.answer, sources: res.sources }]);

      // Update sessions list
      apiListSessions().then(setSessions).catch(() => {});
    } catch (err) {
      setError(err.message);
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    setActiveSession(null);
    setMessages([]);
    setError('');
  }

  function handleSessionClick(sessionId) {
    setActiveSession(sessionId);
    setError('');
  }

  return (
    <div className="chat-layout">
      {/* Sidebar */}
      <aside className="chat-sidebar">
        <button className="btn btn-primary btn-new-chat" onClick={handleNewChat} id="new-chat-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Chat
        </button>

        {/* Document filter */}
        <div className="sidebar-section">
          <label className="label">Filter by document</label>
          <select
            className="input"
            value={selectedDoc ?? ''}
            onChange={(e) => setSelectedDoc(e.target.value ? Number(e.target.value) : null)}
            id="doc-filter-select"
          >
            <option value="">All documents</option>
            {documents.map(d => (
              <option key={d.id} value={d.id}>{d.original_name}</option>
            ))}
          </select>
        </div>

        {/* Session list */}
        <div className="sidebar-section">
          <label className="label">History</label>
          <div className="session-list">
            {sessions.length === 0 ? (
              <p className="session-empty">No chats yet</p>
            ) : sessions.map(s => (
              <button
                key={s.id}
                className={`session-item ${s.id === activeSession ? 'active' : ''}`}
                onClick={() => handleSessionClick(s.id)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <span className="session-title">{s.title}</span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Main chat area */}
      <main className="chat-main">
        <div className="chat-messages">
          {messages.length === 0 && !loading ? (
            <div className="chat-welcome fade-in">
              <div className="welcome-icon">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <circle cx="10" cy="16" r="2"/>
                  <path d="m20 16-1.5-1.5"/>
                  <path d="M12 16h6"/>
                </svg>
              </div>
              <h2>Chat with your documents</h2>
              <p>Ask any question about your uploaded PDFs.</p>
              <p>
                {selectedDoc
                  ? `Searching in: ${documents.find(d => d.id === selectedDoc)?.original_name}`
                  : 'Searching across all your documents'
                }
              </p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <ChatMessage key={i} role={msg.role} content={msg.content} sources={msg.sources} />
            ))
          )}

          {loading && (
            <div className="chat-thinking fade-in">
              <div className="spinner" />
              <span>Thinking…</span>
            </div>
          )}

          {error && <div className="alert alert-error" style={{ margin: '16px 0' }}>{error}</div>}

          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <form className="chat-input-bar" onSubmit={handleSubmit}>
          <input
            className="input chat-input"
            type="text"
            placeholder="Ask a question about your documents…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            id="chat-query-input"
            autoComplete="off"
          />
          <button className="btn btn-primary chat-send-btn" type="submit" disabled={loading || !query.trim()} id="chat-send-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </form>
      </main>
    </div>
  );
}
