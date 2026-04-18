/**
 * API client — wraps fetch with base URL.
 *
 * In dev it hits localhost:8000; in production (Vercel) it reads VITE_API_URL.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(endpoint, { method = 'GET', body, headers = {}, isFormData = false } = {}) {
  const opts = {
    method,
    headers: {
      ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...headers,
    },
  };

  if (body) {
    opts.body = isFormData ? body : JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${endpoint}`, opts);

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const msg = data?.detail || `Request failed (${res.status})`;
    throw new Error(msg);
  }

  return data;
}

/* ---------- Documents ---------- */

export async function apiUploadDocument(file) {
  const form = new FormData();
  form.append('file', file);
  return request('/api/documents/upload', { method: 'POST', body: form, isFormData: true });
}

export async function apiListDocuments() {
  return request('/api/documents');
}

export async function apiGetDocument(id) {
  return request(`/api/documents/${id}`);
}

export async function apiDeleteDocument(id) {
  return request(`/api/documents/${id}`, { method: 'DELETE' });
}

/* ---------- Chat ---------- */

export async function apiAskQuestion(query, documentId = null, sessionId = null, topK = 5) {
  return request('/api/chat', {
    method: 'POST',
    body: { query, document_id: documentId, session_id: sessionId, top_k: topK },
  });
}

export async function apiListSessions() {
  return request('/api/chat/sessions');
}

export async function apiGetSessionMessages(sessionId) {
  return request(`/api/chat/sessions/${sessionId}/messages`);
}

export async function apiCreateSession(title = 'New Chat', documentId = null) {
  return request('/api/chat/sessions', {
    method: 'POST',
    body: { title, document_id: documentId },
  });
}
