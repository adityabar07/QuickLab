import React, { useState, useEffect, useCallback } from 'react';
import ExecutionControls from './components/ExecutionControls';
import Sidebar from './components/Sidebar';
import CodeEditor from './components/CodeEditor';
import TerminalOutput from './components/TerminalOutput';
import { useSession } from './hooks/useSession';
import { usePythonExecution } from './hooks/usePythonExecution';
import './App.css';

const DEFAULT_WELCOME_CODE = `# Welcome to QuickLab V1!
# All 7 standard libraries are pre-installed and ready out-of-the-box.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy
import sympy as sp
import sklearn

print("✓ QuickLab V1 (Python 3.11) Environment Ready!")
df = pd.DataFrame({
    "Library": ["NumPy", "Pandas", "Matplotlib", "Seaborn", "SciPy", "SymPy", "Scikit-learn"],
    "Status": ["Pre-installed", "Pre-installed", "Pre-installed", "Pre-installed", "Pre-installed", "Pre-installed", "Pre-installed"]
})
df
`;

export default function App() {
  const [cells, setCells] = useState([
    { id: 'c1', type: 'code', source: DEFAULT_WELCOME_CODE, outputs: [], execCount: null, collapsed: false }
  ]);
  const [selectedId, setSelectedId] = useState('c1');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState('dark');

  const {
    sessionId,
    kernelStatus,
    setKernelStatus,
    variables,
    setVariables,
    packages,
    files,
    uploadFile,
    deleteFile,
    restartKernel
  } = useSession();

  const { isRunning, executeCode } = usePythonExecution(
    sessionId,
    (newVars) => setVariables(newVars),
    (status) => setKernelStatus(status)
  );

  // Toggle theme class on HTML element
  useEffect(() => {
    document.documentElement.classList.toggle('light', theme === 'light');
  }, [theme]);

  const addCell = useCallback((type = 'code', source = '', afterId = null) => {
    const newCell = {
      id: 'c_' + Math.random().toString(36).substring(2, 9),
      type,
      source,
      outputs: [],
      execCount: null,
      collapsed: false
    };

    setCells(prev => {
      if (!afterId) return [...prev, newCell];
      const idx = prev.findIndex(c => c.id === afterId);
      if (idx === -1) return [...prev, newCell];
      const copy = [...prev];
      copy.splice(idx + 1, 0, newCell);
      return copy;
    });

    setSelectedId(newCell.id);
  }, []);

  const updateCellSource = useCallback((id, source) => {
    setCells(prev => prev.map(c => c.id === id ? { ...c, source } : c));
  }, []);

  const deleteCell = useCallback((id) => {
    setCells(prev => {
      if (prev.length <= 1) return prev;
      const idx = prev.findIndex(c => c.id === id);
      const filtered = prev.filter(c => c.id !== id);
      if (selectedId === id) {
        setSelectedId(filtered[Math.max(0, idx - 1)].id);
      }
      return filtered;
    });
  }, [selectedId]);

  const runCell = useCallback(async (id, advance = true) => {
    const cell = cells.find(c => c.id === id);
    if (!cell) return;

    if (cell.type === 'markdown') return;

    const { outputs, execCount } = await executeCode(cell.source);
    setCells(prev => prev.map(c => c.id === id ? { ...c, outputs, execCount } : c));

    if (advance) {
      const idx = cells.findIndex(c => c.id === id);
      if (idx === cells.length - 1) {
        addCell('code', '', id);
      } else {
        setSelectedId(cells[idx + 1].id);
      }
    }
  }, [cells, executeCode, addCell]);

  const runAllCells = useCallback(async () => {
    for (const cell of cells) {
      if (cell.type === 'code') {
        const { outputs, execCount } = await executeCode(cell.source);
        setCells(prev => prev.map(c => c.id === cell.id ? { ...c, outputs, execCount } : c));
      }
    }
  }, [cells, executeCode]);

  const clearOutputs = useCallback(() => {
    setCells(prev => prev.map(c => ({ ...c, outputs: [], execCount: null })));
  }, []);

  const exportIpynb = useCallback(() => {
    const nb = {
      cells: cells.map(c => ({
        cell_type: c.type === 'markdown' ? 'markdown' : 'code',
        metadata: {},
        source: c.source.split('\n').map((l, i, arr) => i < arr.length - 1 ? l + '\n' : l),
        ...(c.type === 'code' ? {
          execution_count: c.execCount,
          outputs: c.outputs.filter(o => o.kind === 'stream' || o.kind === 'result').map(o => ({
            output_type: 'stream',
            name: 'stdout',
            text: [o.text]
          }))
        } : {})
      })),
      metadata: {
        kernelspec: { display_name: 'Python 3.11 (QuickLab)', language: 'python', name: 'python3' },
        language_info: { name: 'python' }
      },
      nbformat: 4,
      nbformat_minor: 5
    };

    const blob = new Blob([JSON.stringify(nb, null, 2)], { type: 'application/x-ipynb+json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'quicklab-notebook.ipynb';
    document.body.appendChild(a);
    a.click();
    a.remove();
  }, [cells]);

  return (
    <div id="app">
      <ExecutionControls
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onAddCode={() => addCell('code')}
        onAddMarkdown={() => addCell('markdown')}
        onRunAll={runAllCells}
        onRestartKernel={restartKernel}
        onClearOutputs={clearOutputs}
        kernelStatus={kernelStatus}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onExportIpynb={exportIpynb}
      />

      <div id="body">
        <Sidebar
          isOpen={sidebarOpen}
          cells={cells}
          selectedId={selectedId}
          onSelectCell={setSelectedId}
          packages={packages}
          variables={variables}
          files={files}
          onUploadFile={uploadFile}
          onDeleteFile={deleteFile}
        />

        <div id="notebook-wrap">
          <div id="notebook">
            {cells.map((cell) => {
              const isSelected = cell.id === selectedId;
              return (
                <div
                  key={cell.id}
                  className={`cell ${isSelected ? 'selected' : ''}`}
                  onClick={() => setSelectedId(cell.id)}
                >
                  <div className="cell-gutter">
                    {cell.type === 'code' && (
                      <div className="exec-count">
                        <span className="brk">In [</span>
                        {cell.execCount ?? ' '}
                        <span className="brk">]</span>
                      </div>
                    )}
                  </div>

                  <div className="cell-main">
                    <div className="cell-toolbar">
                      <span className={`cell-type-tag ${cell.type === 'markdown' ? 'md' : ''}`}>
                        {cell.type === 'markdown' ? 'markdown' : 'python'}
                      </span>

                      <button
                        className="cbtn"
                        title="Run cell (Shift+Enter)"
                        onClick={() => runCell(cell.id, true)}
                      >
                        ▶
                      </button>

                      <button
                        className="cbtn"
                        title="Delete cell"
                        onClick={() => deleteCell(cell.id)}
                      >
                        ✕
                      </button>
                    </div>

                    <CodeEditor
                      value={cell.source}
                      onChange={(val) => updateCellSource(cell.id, val)}
                      onRun={() => runCell(cell.id, true)}
                      onRunInPlace={() => runCell(cell.id, false)}
                      mode={cell.type === 'markdown' ? 'markdown' : 'python'}
                      theme={theme}
                    />

                    {cell.type === 'code' && (
                      <TerminalOutput
                        outputs={cell.outputs}
                        isRunning={isRunning && isSelected}
                      />
                    )}
                  </div>
                </div>
              );
            })}

            <div className="add-cell-row">
              <button onClick={() => addCell('code')}>+ Code</button>
              <button onClick={() => addCell('markdown')}>+ Text</button>
            </div>
          </div>
        </div>
      </div>

      <div id="statusbar">
        <span>{cells.length} cell{cells.length === 1 ? '' : 's'}</span>
        <span className="sep"></span>
        <span className="warn-flag">⚠ Ephemeral session — export .ipynb before closing tab</span>
      </div>
    </div>
  );
}
