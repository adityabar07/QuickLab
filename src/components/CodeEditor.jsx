import React, { useRef, useEffect } from 'react';

export default function CodeEditor({
  value,
  onChange,
  onRun,
  onRunInPlace,
  mode = 'python',
  theme = 'dark',
  autoFocus = false
}) {
  const editorRef = useRef(null);
  const cmInstance = useRef(null);

  useEffect(() => {
    if (!editorRef.current) return;

    // Check if global CodeMirror is available via CDN
    if (window.CodeMirror) {
      if (!cmInstance.current) {
        const cm = window.CodeMirror(editorRef.current, {
          value: value || '',
          mode: mode === 'python' ? 'python' : 'markdown',
          theme: theme === 'dark' ? 'material-darker' : 'default',
          lineNumbers: true,
          indentUnit: 4,
          tabSize: 4,
          lineWrapping: true,
          viewportMargin: Infinity,
          extraKeys: {
            'Shift-Enter': () => { if (onRun) onRun(); },
            'Ctrl-Enter': () => { if (onRunInPlace) onRunInPlace(); },
            'Cmd-Enter': () => { if (onRunInPlace) onRunInPlace(); },
            'Tab': (cm) => { cm.replaceSelection('    ', 'end'); }
          }
        });

        cm.on('change', () => {
          const val = cm.getValue();
          if (onChange) onChange(val);
        });

        cmInstance.current = cm;
        if (autoFocus) cm.focus();
      } else {
        if (cmInstance.current.getValue() !== value) {
          cmInstance.current.setValue(value || '');
        }
        cmInstance.current.setOption('theme', theme === 'dark' ? 'material-darker' : 'default');
      }
    }
  }, [mode, theme, autoFocus, onChange, onRun, onRunInPlace, value]);

  // Fallback if CodeMirror is not loaded
  if (!window.CodeMirror) {
    return (
      <div className="editor-host fallback">
        <textarea
          value={value}
          onChange={(e) => onChange && onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.shiftKey) {
              e.preventDefault();
              if (onRun) onRun();
            } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              if (onRunInPlace) onRunInPlace();
            } else if (e.key === 'Tab') {
              e.preventDefault();
              const start = e.target.selectionStart;
              const end = e.target.selectionEnd;
              const newVal = value.substring(0, start) + '    ' + value.substring(end);
              if (onChange) onChange(newVal);
            }
          }}
          className="fallback-textarea"
          rows={Math.max(3, (value || '').split('\n').length + 1)}
          placeholder={mode === 'python' ? 'Write Python code here…' : 'Write Markdown text here…'}
        />
      </div>
    );
  }

  return <div ref={editorRef} className="editor-host" />;
}
