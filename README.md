# QuickLab

Instant, anonymous in-browser Python notebook powered by Pyodide (WebAssembly), CodeMirror, and client-side data science tools.

## Features
- **Zero Backend / No Login**: 100% client-side execution in your browser tab.
- **Python Data Science Stack**: Preloaded with NumPy, Pandas, Matplotlib, SciPy, Scikit-Learn, SymPy, NetworkX, and BeautifulSoup.
- **Interactive Visualizations**: Matplotlib figures captured and rendered inline automatically.
- **Session File System**: Drag and drop CSV, Excel, JSON, and text files directly into the in-memory Pyodide filesystem (`/home/pyodide/`).
- **Jupyter & JSON Compatibility**: Export and import standard `.ipynb` notebooks or lightweight `.json` files.
- **Command Palette & Keyboard Shortcuts**: Fast navigation with full Jupyter-style keybindings (`Shift+Enter`, `Ctrl+Shift+P`, `A`, `B`, `D`, `M`, `Y`).
- **Dark / Light Mode**: Seamless theme switching.

## Getting Started

```bash
npm install
npm run dev
```
