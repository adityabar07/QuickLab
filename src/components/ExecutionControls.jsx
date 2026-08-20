import React from 'react';

export default function ExecutionControls({
  onAddCode,
  onAddMarkdown,
  onRunAll,
  onRestartKernel,
  onClearOutputs,
  onToggleSidebar,
  sidebarOpen,
  kernelStatus,
  theme,
  onToggleTheme,
  onExportJson,
  onExportIpynb,
  onImport
}) {
  return (
    <div id="topbar">
      <button
        className={`tbtn ${sidebarOpen ? 'active' : ''}`}
        onClick={onToggleSidebar}
        title="Toggle sidebar (Ctrl+B)"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M9 4v16" />
        </svg>
      </button>

      <div className="brand">
        <div className="mark">Q</div>
        QuickLab <span className="tag">no login · pre-installed libraries</span>
      </div>

      <div className="divider"></div>

      <button className="tbtn" onClick={onAddCode} title="Add code cell (B)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14" />
        </svg>
        Code
      </button>

      <button className="tbtn" onClick={onAddMarkdown} title="Add text cell">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14" />
        </svg>
        Text
      </button>

      <button className="tbtn primary" onClick={onRunAll} title="Run all cells">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z" />
        </svg>
        Run all
      </button>

      <button className="tbtn" onClick={onRestartKernel} title="Restart kernel & clear session memory">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 11-.57-8.38l5.67-5.67" />
        </svg>
        Restart
      </button>

      <button className="tbtn" onClick={onClearOutputs} title="Clear all outputs">
        Clear outputs
      </button>

      <div className="divider"></div>

      <div className="menu-wrap dropdown-container">
        <button className="tbtn" onClick={onExportIpynb} title="Export as Jupyter Notebook (.ipynb)">
          Export .ipynb
        </button>
      </div>

      <div id="topbar-spacer"></div>

      <div className="kernel-pill">
        <span className={`dot ${kernelStatus.state}`}></span>
        <span>{kernelStatus.label}</span>
      </div>

      <button className="tbtn" onClick={onToggleTheme} title="Toggle theme">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      </button>
    </div>
  );
}
