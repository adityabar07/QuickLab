import React, { useState } from 'react';
import { aiFixError } from '../lib/api';

export default function TerminalOutput({
  outputs = [],
  isRunning = false,
  cellSource = '',
  onApplyFix = null
}) {
  const [aiLoading, setAiLoading] = useState(false);
  const [aiFixResult, setAiFixResult] = useState(null);
  const [aiError, setAiError] = useState(null);

  const handleFixError = async (errText) => {
    setAiLoading(true);
    setAiError(null);
    try {
      const data = await aiFixError(cellSource, errText);
      setAiFixResult(data.fix);
    } catch (err) {
      setAiError(err.message || 'Could not contact Gemini AI service.');
    } finally {
      setAiLoading(false);
    }
  };

  const extractCodeBlock = (markdownText) => {
    if (!markdownText) return null;
    const match = markdownText.match(/```python\s*([\s\S]*?)\s*```/);
    return match ? match[1] : null;
  };

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
          const suggestedCode = aiFixResult ? extractCodeBlock(aiFixResult) : null;
          return (
            <div key={idx} className="out-block out-error-wrap">
              <div className="out-error">{out.text}</div>
              
              {/* AI Fix Assistant Button */}
              <div className="ai-fix-bar">
                <button
                  className="ai-btn"
                  onClick={() => handleFixError(out.text)}
                  disabled={aiLoading}
                  title="Ask Gemini AI to analyze traceback and suggest fix"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
                  </svg>
                  {aiLoading ? 'Analyzing with Gemini…' : 'Explain & Fix Error with AI'}
                </button>
              </div>

              {/* AI Response Card */}
              {aiFixResult && (
                <div className="ai-result-card">
                  <div className="ai-result-header">
                    <span className="ai-tag">✨ Gemini AI Diagnosis</span>
                    {suggestedCode && onApplyFix && (
                      <button
                        className="ai-apply-btn"
                        onClick={() => onApplyFix(suggestedCode)}
                        title="Apply suggested code fix into cell"
                      >
                        Apply Fix to Cell
                      </button>
                    )}
                  </div>
                  <div className="ai-result-body">
                    <pre className="ai-result-text">{aiFixResult}</pre>
                  </div>
                </div>
              )}

              {aiError && (
                <div className="ai-err-msg">
                  ⚠ {aiError}
                </div>
              )}
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
