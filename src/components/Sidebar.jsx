import React, { useState } from 'react';

export default function Sidebar({
  isOpen,
  cells,
  selectedId,
  onSelectCell,
  packages,
  variables,
  files,
  onUploadFile,
  onDeleteFile
}) {
  const [activeTab, setActiveTab] = useState('outline');
  const [pkgSearch, setPkgSearch] = useState('');

  if (!isOpen) {
    return <div id="sidebar" className="collapsed" />;
  }

  const filteredPackages = packages.filter(p =>
    p.name.toLowerCase().includes(pkgSearch.toLowerCase()) ||
    p.category.toLowerCase().includes(pkgSearch.toLowerCase()) ||
    p.description.toLowerCase().includes(pkgSearch.toLowerCase())
  );

  return (
    <div id="sidebar">
      <div className="side-nav">
        <button
          className={`side-nav-btn ${activeTab === 'outline' ? 'active' : ''}`}
          onClick={() => setActiveTab('outline')}
        >
          Outline
        </button>
        <button
          className={`side-nav-btn ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          Files
        </button>
        <button
          className={`side-nav-btn ${activeTab === 'packages' ? 'active' : ''}`}
          onClick={() => setActiveTab('packages')}
        >
          Packages
        </button>
        <button
          className={`side-nav-btn ${activeTab === 'variables' ? 'active' : ''}`}
          onClick={() => setActiveTab('variables')}
        >
          Variables
        </button>
      </div>

      {/* Outline Tab */}
      {activeTab === 'outline' && (
        <div className="tab-pane active" id="tab-outline">
          <div className="side-section">
            <div className="side-title">Notebook Outline</div>
          </div>
          <div id="outline">
            {cells.map((c, i) => {
              const firstLine = (c.source.split('\n')[0] || (c.type === 'markdown' ? 'Empty text cell' : 'Empty cell')).slice(0, 36);
              return (
                <div
                  key={c.id}
                  className={`outline-item ${c.type === 'markdown' ? 'md' : ''} ${c.id === selectedId ? 'active' : ''}`}
                  onClick={() => onSelectCell(c.id)}
                >
                  <span className="badge">{i + 1}</span>
                  <span className="lbl">{firstLine}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Files Tab */}
      {activeTab === 'files' && (
        <div className="tab-pane active" id="tab-files">
          <div className="side-section">
            <div className="side-title">Session Files</div>
          </div>
          <label className="upload-zone" htmlFor="file-uploader">
            Drop files here or click<br />csv · json · txt
            <input
              id="file-uploader"
              type="file"
              multiple
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files) {
                  Array.from(e.target.files).forEach(f => onUploadFile(f));
                }
              }}
            />
          </label>
          <div id="file-list">
            {files.map(f => (
              <div key={f.name} className="file-item">
                <span className="fname" title={f.name}>{f.name}</span>
                <span>{(f.size / 1024).toFixed(1)}kb</span>
                <button onClick={() => onDeleteFile(f.name)} title="Remove">✕</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Packages Tab */}
      {activeTab === 'packages' && (
        <div className="tab-pane active" id="tab-packages">
          <input
            type="text"
            id="pkg-search"
            placeholder="Search pre-installed packages…"
            value={pkgSearch}
            onChange={(e) => setPkgSearch(e.target.value)}
          />
          <div id="pkg-list">
            {filteredPackages.map(p => (
              <div key={p.name} className="pkg-card">
                <div className="pkg-head">
                  <span>{p.name}</span>
                  <span className="pkg-cat">{p.category}</span>
                </div>
                <div className="pkg-desc">{p.description}</div>
                <div className="pkg-ver">Version: {p.version}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Variables Tab */}
      {activeTab === 'variables' && (
        <div className="tab-pane active" id="tab-variables">
          <div className="side-section">
            <div className="side-title">Session Variables</div>
          </div>
          <div id="var-list">
            {variables.length === 0 ? (
              <div style={{ color: 'var(--text-faint)', padding: '10px 14px', fontStyle: 'italic' }}>
                No active variables in memory.
              </div>
            ) : (
              variables.map(v => (
                <div key={v.name} className="var-card">
                  <div>
                    <span className="var-name">{v.name}</span>
                    <span className="var-type">{v.type} {v.shape || ''}</span>
                  </div>
                  <div className="var-val">{v.preview}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div id="sidebar-footer">
        <b>QuickLab V1 (Python 3.11).</b><br />
        Pre-installed libraries: NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, Scikit-learn.
      </div>
    </div>
  );
}
