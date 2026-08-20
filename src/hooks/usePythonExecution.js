import { useState, useCallback } from 'react';

export function usePythonExecution(sessionId, onVariablesUpdate, onStatusChange) {
  const [execSeq, setExecSeq] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const executeCode = useCallback(async (code) => {
    if (!code.trim()) {
      return { outputs: [], execCount: null };
    }

    setIsRunning(true);
    if (onStatusChange) onStatusChange({ state: 'busy', label: 'running…' });

    let outputs = [];
    let nextSeq = execSeq + 1;

    try {
      const res = await fetch('/api/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, session_id: sessionId })
      });

      if (res.ok) {
        const data = await res.json();
        outputs = data.outputs || [];
        nextSeq = data.exec_count || nextSeq;
        if (data.variables && onVariablesUpdate) {
          onVariablesUpdate(data.variables);
        }
      } else {
        outputs.push({ kind: 'error', text: `Server error: HTTP ${res.status} ${res.statusText}` });
      }
    } catch (err) {
      outputs.push({
        kind: 'error',
        text: 'Python execution backend is offline.\n\nStart the QuickLab backend / Docker environment (port 8000) to run Python.'
      });
      if (onStatusChange) onStatusChange({ state: 'offline', label: 'Python Backend Offline' });
    } finally {
      setIsRunning(false);
      setExecSeq(nextSeq);
      if (onStatusChange) onStatusChange({ state: 'ready', label: 'Python 3.11 — Docker' });
    }

    return { outputs, execCount: nextSeq };
  }, [sessionId, execSeq, onVariablesUpdate, onStatusChange]);

  return {
    execSeq,
    setExecSeq,
    isRunning,
    executeCode
  };
}
