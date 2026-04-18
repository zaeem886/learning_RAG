import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14 2 14 8 20 8"/>
            <circle cx="10" cy="16" r="2"/>
            <path d="m20 16-1.5-1.5"/>
            <path d="M12 16h6"/>
          </svg>
          <span>DocChat AI</span>
        </Link>

        <div className="navbar-right">
          <Link to="/" className="nav-link">Documents</Link>
          <Link to="/chat" className="nav-link">Chat</Link>
        </div>
      </div>
    </nav>
  );
}
