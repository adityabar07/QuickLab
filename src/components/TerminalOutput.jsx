import React from 'react';

export default function TerminalOutput({ outputs = [], isRunning = false }) {
  if (!outputs || outputs.length === 0) {
    if (isRunning) {
      return (
        <div className="cell-output">
          <div className="out-block out-stream text-warn animate-pulse">Running execution…</div>
        </div>
      );
    }
    return null;
  }

  return (
    <div className="cell-output">
      {outputs.map((out, idx) => {
        if (out.kind === 'stream') {
          return (
            <div key={idx} className="out-block out-stream">
              {out.text}
            </div>
          );
        }
        if (out.kind === 'error') {
          return (
            <div key={idx} className="out-block out-error">
              {out.text}
            </div>
          );
        }
        if (out.kind === 'result') {
          return (
            <div key={idx} className="out-block out-result">
              {out.text}
            </div>
          );
        }
        if (out.kind === 'image') {
          return (
            <div key={idx} className="out-block out-img">
              <img
                src={`data:image/png;base64,${out.data}`}
                alt="Matplotlib / Seaborn figure"
                className="max-w-full rounded border border-border"
              />
            </div>
          );
        }
        if (out.kind === 'html') {
          return (
            <div
              key={idx}
              className="out-block out-table"
              dangerouslySetInnerHTML={{ __html: out.data }}
            />
          );
        }
        return null;
      })}
    </div>
  );
}
