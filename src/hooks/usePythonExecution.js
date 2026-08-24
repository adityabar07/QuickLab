import { useState, useCallback } from 'react';
import { executeCode as apiExecuteCode } from '../lib/api';

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
      const data = await apiExecuteCode(code, sessionId);
      outputs = data.outputs || [];
      nextSeq = data.exec_count || nextSeq;
      if (data.variables && onVariablesUpdate) {
        onVariablesUpdate(data.variables);
      }
    } catch (err) {
      outputs.push({
        kind: 'error',
        text: err.message || 'Python execution failed. Please verify backend connection.'
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
