import { useState, useEffect, useCallback } from 'react';

export function useSession() {
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substring(2, 10));
  const [backendOnline, setBackendOnline] = useState(false);
  const [kernelStatus, setKernelStatus] = useState({ state: 'loading', label: 'checking backend…' });
  const [variables, setVariables] = useState([]);
  const [packages, setPackages] = useState([]);
  const [files, setFiles] = useState([]);

  // Check backend health
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/health', { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        setBackendOnline(true);
        setKernelStatus({ state: 'ready', label: 'Python 3.11 — Docker' });
        return true;
      }
    } catch {
      // Backend unreachable
    }
    setBackendOnline(false);
    setKernelStatus({ state: 'offline', label: 'Python Backend Offline' });
    return false;
  }, []);

  // Fetch package catalog
  const fetchPackages = useCallback(async () => {
    try {
      const res = await fetch('/api/packages');
      if (res.ok) {
        const data = await res.json();
        setPackages(data.packages || []);
      }
    } catch {}
  }, []);

  // Fetch session files
  const fetchFiles = useCallback(async () => {
    try {
      const res = await fetch(`/api/files/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setFiles(data.files || []);
      }
    } catch {}
  }, [sessionId]);

  // Upload file to session
  const uploadFile = useCallback(async (file) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('file', file);
    try {
      const res = await fetch('/api/files/upload', { method: 'POST', body: formData });
      if (res.ok) {
        await fetchFiles();
        return true;
      }
    } catch {}
    return false;
  }, [sessionId, fetchFiles]);

  // Delete file from session
  const deleteFile = useCallback(async (filename) => {
    try {
      await fetch(`/api/files/${sessionId}/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      await fetchFiles();
    } catch {}
  }, [sessionId, fetchFiles]);

  // Restart kernel
  const restartKernel = useCallback(async () => {
    setKernelStatus({ state: 'busy', label: 'restarting…' });
    try {
      await fetch('/api/restart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      setVariables([]);
    } catch {}
    setKernelStatus({ state: backendOnline ? 'ready' : 'offline', label: backendOnline ? 'Python 3.11 — Docker' : 'Python Backend Offline' });
  }, [sessionId, backendOnline]);

  useEffect(() => {
    checkHealth().then((isUp) => {
      if (isUp) {
        fetchPackages();
        fetchFiles();
      }
    });

    const interval = setInterval(() => {
      checkHealth();
    }, 5000);
    return () => clearInterval(interval);
  }, [checkHealth, fetchPackages, fetchFiles]);

  return {
    sessionId,
    backendOnline,
    kernelStatus,
    setKernelStatus,
    variables,
    setVariables,
    packages,
    files,
    uploadFile,
    deleteFile,
    restartKernel,
    checkHealth
  };
}
