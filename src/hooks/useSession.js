import { useState, useEffect, useCallback } from 'react';
import {
  checkBackendHealth,
  fetchPackages as apiFetchPackages,
  fetchSessionFiles,
  uploadSessionFile,
  deleteSessionFile,
  restartKernel as apiRestartKernel
} from '../lib/api';

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
      const data = await checkBackendHealth();
      if (data && data.status === 'ok') {
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
      const data = await apiFetchPackages();
      setPackages(data.packages || []);
    } catch {}
  }, []);

  // Fetch session files
  const fetchFiles = useCallback(async () => {
    try {
      const data = await fetchSessionFiles(sessionId);
      setFiles(data.files || []);
    } catch {}
  }, [sessionId]);

  // Upload file to session
  const uploadFile = useCallback(async (file) => {
    try {
      await uploadSessionFile(sessionId, file);
      await fetchFiles();
      return true;
    } catch (err) {
      console.error("Upload error:", err);
      return false;
    }
  }, [sessionId, fetchFiles]);

  // Delete file from session
  const deleteFile = useCallback(async (filename) => {
    try {
      await deleteSessionFile(sessionId, filename);
      await fetchFiles();
    } catch {}
  }, [sessionId, fetchFiles]);

  // Restart kernel
  const restartKernel = useCallback(async () => {
    setKernelStatus({ state: 'busy', label: 'restarting…' });
    try {
      await apiRestartKernel(sessionId);
      setVariables([]);
    } catch {}
    setKernelStatus({
      state: backendOnline ? 'ready' : 'offline',
      label: backendOnline ? 'Python 3.11 — Docker' : 'Python Backend Offline'
    });
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
    }, 6000);
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
