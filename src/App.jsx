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

  const moveCell = useCallback((id, direction) => {
    setCells(prev => {
      const idx = prev.findIndex(c => c.id === id);
      if (idx === -1) return prev;
      const targetIdx = idx + direction;
      if (targetIdx < 0 || targetIdx >= prev.length) return prev;
      const copy = [...prev];
      const [item] = copy.splice(idx, 1);
      copy.splice(targetIdx, 0, item);
      return copy;
    });
  }, []);

  const duplicateCell = useCallback((id) => {
    setCells(prev => {
      const idx = prev.findIndex(c => c.id === id);
      if (idx === -1) return prev;
      const target = prev[idx];
      const dup = {
        ...target,
        id: 'c_' + Math.random().toString(36).substring(2, 9),
        outputs: [],
        execCount: null
      };
      const copy = [...prev];
      copy.splice(idx + 1, 0, dup);
      return copy;
    });
  }, []);

  const toggleCollapse = useCallback((id) => {
    setCells(prev => prev.map(c => c.id === id ? { ...c, collapsed: !c.collapsed } : c));
  }, []);

  const convertCellType = useCallback((id) => {
    setCells(prev => prev.map(c => {
      if (c.id !== id) return c;
      const newType = c.type === 'code' ? 'markdown' : 'code';
      return { ...c, type: newType, outputs: [] };
    }));
  }, []);

  const runCell = useCallback(async (id, advance = true) => {
    const cell = cells.find(c => c.id === id);
    if (!cell) return;

    if (cell.type === 'markdown') {
      if (advance) {
        const idx = cells.findIndex(c => c.id === id);
        if (idx === cells.length - 1) {
          addCell('code', '', id);
        } else {
          setSelectedId(cells[idx + 1].id);
        }
      }
      return;
    }

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
                  className={`cell ${isSelected ? 'selected' : ''} ${cell.collapsed ? 'collapsed' : ''}`}
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

                      {/* 1. Run / Render */}
                      <button
                        className="cbtn"
                        title={cell.type === 'code' ? 'Run cell (Shift+Enter)' : 'Render (Shift+Enter)'}
                        onClick={(e) => { e.stopPropagation(); runCell(cell.id, true); }}
                      >
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </button>

                      {/* 2. Move Up */}
                      <button
                        className="cbtn"
                        title="Move up"
                        onClick={(e) => { e.stopPropagation(); moveCell(cell.id, -1); }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M12 19V5M5 12l7-7 7 7" />
                        </svg>
                      </button>

                      {/* 3. Move Down */}
                      <button
                        className="cbtn"
                        title="Move down"
                        onClick={(e) => { e.stopPropagation(); moveCell(cell.id, 1); }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M12 5v14M5 12l7 7 7-7" />
                        </svg>
                      </button>

                      {/* 4. Duplicate */}
                      <button
                        className="cbtn"
                        title="Duplicate cell"
                        onClick={(e) => { e.stopPropagation(); duplicateCell(cell.id); }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="9" y="9" width="12" height="12" rx="2" />
                          <path d="M5 15V5a2 2 0 012-2h10" />
                        </svg>
                      </button>

                      {/* 5. Collapse / Expand */}
                      <button
                        className="cbtn"
                        title={cell.collapsed ? 'Expand cell' : 'Collapse cell'}
                        onClick={(e) => { e.stopPropagation(); toggleCollapse(cell.id); }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d={cell.collapsed ? 'M9 6l6 6-6 6' : 'M6 9l6 6 6-6'} />
                        </svg>
                      </button>

                      {/* 6. Convert Type (Python <-> Markdown) */}
                      <button
                        className="cbtn"
                        title={cell.type === 'code' ? 'Convert to Markdown' : 'Convert to Python Code'}
                        onClick={(e) => { e.stopPropagation(); convertCellType(cell.id); }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M7 16V4M7 4l-3 3M7 4l3 3M17 8v12m0 0l3-3m-3 3l-3-3" />
                        </svg>
                      </button>

                      {/* 7. Delete */}
                      <button
                        className="cbtn"
                        title="Delete cell"
                        onClick={(e) => { e.stopPropagation(); deleteCell(cell.id); }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0-1 14a2 2 0 01-2 2H7a2 2 0 01-2-2L4 6" />
                        </svg>
                      </button>
                    </div>

                    {!cell.collapsed ? (
                      <>
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
                      </>
                    ) : (
                      <div className="collapsed-hint">
                        Cell collapsed — click expand in top-right to view.
                      </div>
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
