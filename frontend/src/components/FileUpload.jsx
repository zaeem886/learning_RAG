import { useRef, useState } from 'react';
import './FileUpload.css';

export default function FileUpload({ onUpload, uploading }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer?.files?.[0];
    if (file && file.type === 'application/pdf') onUpload(file);
  }

  function handleChange(e) {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
  }

  return (
    <div
      className={`file-upload ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={handleChange}
        style={{ display: 'none' }}
        id="file-upload-input"
      />

      {uploading ? (
        <div className="upload-status">
          <div className="spinner" />
          <p>Processing your document…</p>
        </div>
      ) : (
        <>
          <div className="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <p className="upload-text">
            <strong>Drop your PDF here</strong> or click to browse
          </p>
          <p className="upload-hint">Maximum file size: 50 MB</p>
        </>
      )}
    </div>
  );
}
