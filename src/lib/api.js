/**
 * QuickLab Centralized API & WebSocket Client
 * Automatically handles development (Vite proxy) and production (Vercel + Backend) routing.
 */

// Resolves base API URL from environment variable or defaults to empty (Vite local proxy)
const RAW_API_URL = import.meta.env.VITE_API_URL || '';
export const API_BASE = RAW_API_URL.replace(/\/+$/, '');

/**
 * Returns a fully qualified API endpoint URL.
 * @param {string} path - API endpoint path (e.g. '/api/health')
 * @returns {string}
 */
export function getApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return API_BASE ? `${API_BASE}${cleanPath}` : cleanPath;
}

/**
 * Converts HTTP/HTTPS API base URL to standard WS/WSS URL for streaming kernels.
 * @param {string} sessionId - Active QuickLab session ID
 * @returns {string}
 */
export function getWebSocketUrl(sessionId) {
  const wsPath = `/ws/kernel/${sessionId}`;
  if (API_BASE) {
    if (API_BASE.startsWith('https://')) {
      return API_BASE.replace(/^https:\/\//, 'wss://') + wsPath;
    }
    if (API_BASE.startsWith('http://')) {
      return API_BASE.replace(/^http:\/\//, 'ws://') + wsPath;
    }
    return `ws://${API_BASE}${wsPath}`;
  }

  // Fallback to current browser host in development
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${wsPath}`;
}

/**
 * Checks FastAPI backend status and runtime engine.
 */
export async function checkBackendHealth() {
  const res = await fetch(getApiUrl('/api/health'), {
    signal: AbortSignal.timeout(4000)
  });
  if (!res.ok) throw new Error(`Health check failed: HTTP ${res.status}`);
  return await res.json();
}

/**
 * Fetches the official 7 pre-installed scientific library versions.
 */
export async function fetchPackages() {
  const res = await fetch(getApiUrl('/api/packages'));
  if (!res.ok) throw new Error(`Failed to fetch packages: HTTP ${res.status}`);
  return await res.json();
}

/**
 * Executes a Python cell payload.
 */
export async function executeCode(code, sessionId, timeout = null) {
  const body = { code, session_id: sessionId };
  if (timeout) body.timeout = timeout;

  const res = await fetch(getApiUrl('/api/execute'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Execution failed with HTTP ${res.status}`);
  }
  return await res.json();
}

/**
 * Restarts the session kernel and wipes variable memory.
 */
export async function restartKernel(sessionId) {
  const res = await fetch(getApiUrl('/api/restart'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  if (!res.ok) throw new Error(`Kernel restart failed: HTTP ${res.status}`);
  return await res.json();
}

/**
 * Fetches session variable list.
 */
export async function fetchVariables(sessionId) {
  const res = await fetch(getApiUrl(`/api/variables/${sessionId}`));
  if (!res.ok) throw new Error(`Failed to fetch variables: HTTP ${res.status}`);
  return await res.json();
}

/**
 * Fetches session uploaded files list.
 */
export async function fetchSessionFiles(sessionId) {
  const res = await fetch(getApiUrl(`/api/files/${sessionId}`));
  if (!res.ok) throw new Error(`Failed to fetch files: HTTP ${res.status}`);
  return await res.json();
}

/**
 * Uploads a data file (.csv, .txt, .json) to the session sandbox.
 */
export async function uploadSessionFile(sessionId, file) {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('file', file);

  const res = await fetch(getApiUrl('/api/files/upload'), {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with HTTP ${res.status}`);
  }
  return await res.json();
}

/**
 * Deletes a file from the session sandbox.
 */
export async function deleteSessionFile(sessionId, filename) {
  const res = await fetch(getApiUrl(`/api/files/${sessionId}/${encodeURIComponent(filename)}`), {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error(`File deletion failed: HTTP ${res.status}`);
  return await res.json();
}

/**
 * AI Assistant: Explains Python code logic using backend Gemini service.
 */
export async function aiExplainCode(code, context = '') {
  const res = await fetch(getApiUrl('/api/ai/explain'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, context })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `AI explanation failed (HTTP ${res.status})`);
  }
  return data;
}

/**
 * AI Assistant: Diagnoses code errors and generates fixes.
 */
export async function aiFixError(code, errorText) {
  const res = await fetch(getApiUrl('/api/ai/fix-error'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, error: errorText })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `AI fix failed (HTTP ${res.status})`);
  }
  return data;
}

/**
 * AI Assistant: Generates Python code from user instructions.
 */
export async function aiGenerateCode(prompt) {
  const res = await fetch(getApiUrl('/api/ai/generate'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `AI generation failed (HTTP ${res.status})`);
  }
  return data;
}
