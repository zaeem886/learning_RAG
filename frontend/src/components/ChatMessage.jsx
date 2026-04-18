import './ChatMessage.css';

export default function ChatMessage({ role, content, sources }) {
  const isUser = role === 'user';

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg-user' : 'chat-msg-assistant'} fade-in`}>
      <div className="chat-msg-avatar">
        {isUser ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
            <path d="M16 14H8a4 4 0 0 0-4 4v2h16v-2a4 4 0 0 0-4-4z"/>
            <line x1="12" y1="18" x2="12" y2="22"/>
          </svg>
        )}
      </div>
      <div className="chat-msg-body">
        <div className="chat-msg-role">{isUser ? 'You' : 'DocChat AI'}</div>
        <div className="chat-msg-content">{content}</div>
        {!isUser && sources && sources.length > 0 && (
          <div className="chat-msg-sources">
            <div className="sources-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              Sources
            </div>
            {sources.map((s, i) => (
              <div key={i} className="source-chip">
                <span className="source-file">{s.source_file}</span>
                {s.page != null && <span className="source-page">p.{s.page + 1}</span>}
                <span className="source-score">{(s.score * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
