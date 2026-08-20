# QuickLab — Instant Interactive Python Notebook (V1)

> **Zero Setup · No Login · No Database · Pre-installed Python 3.11 Environment**

QuickLab is a browser-based interactive Python notebook platform. Users can open the website, start a temporary session, write Python code, and immediately run calculations, data analysis, and visualizations without needing to install standard scientific and machine learning libraries.

---

## ⚡ Core Philosophy: IMPORT → USE → RUN

In QuickLab V1, all **7 official standard libraries** are **pre-installed and immediately available**:

1. **NumPy** (`numpy`) — N-dimensional arrays and numerical math
2. **Pandas** (`pandas`) — Tabular DataFrames and data manipulation
3. **Matplotlib** (`matplotlib`) — 2D plotting, charts, and figures
4. **Seaborn** (`seaborn`) — Statistical graphics, distributions, and heatmaps
5. **SciPy** (`scipy`) — Numerical algorithms and scientific optimization
6. **SymPy** (`sympy`) — Symbolic mathematics, equation solving, and algebra
7. **Scikit-learn** (`sklearn`) — Machine learning models, classifiers, and pipelines

Users **never** need to run `pip install` for these libraries:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy
import sympy as sp
import sklearn
```

---

## 🏗️ Architecture

```text
Browser Client
     │
     ▼ (HTTP / WebSocket)
QuickLab Frontend (Vite / HTML)
     │
     ▼ (REST /api/execute)
QuickLab Backend Server (FastAPI on port 8000)
     │
     ▼ (Isolated Ephemeral Session Namespace)
Docker Container Sandbox (python:3.11-slim-bookworm)
     │
     ├── 7 Pre-installed Standard Libraries
     ├── Headless Matplotlib / Seaborn PNG Plot Capture
     ├── Responsive Pandas HTML Table Rendering
     └── In-Memory Multi-Cell Variable Persistence
```

- **Ephemeral Sessions**: Every user session maintains temporary in-memory variable state between cells.
- **No Login / No Database**: No accounts, passwords, or permanent storage. When the user closes the tab or restarts the kernel, temporary session data is cleared.

---

## 🚀 Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/adityabar07/QuickLab.git
cd QuickLab

# Build and launch QuickLab
docker compose up --build
```

- **Notebook UI**: [http://localhost:5173](http://localhost:5173) (or `http://<LAN-IP>:5173`)
- **Backend API**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 🧪 Environment Verification

Run the automated verification suite to test all 7 libraries and functional examples:

```bash
python scripts/test-python-packages.py
```

Expected output:

```text
========================================
QUICKLAB ENVIRONMENT CHECK
========================================
Python: 3.11.x

✓ NumPy
✓ Pandas
✓ Matplotlib
✓ Seaborn
✓ SciPy
✓ SymPy
✓ Scikit-learn
========================================
ALL 7 PACKAGES PASSED
========================================

--- RUNNING FUNCTIONAL UNIT TESTS ---
  [OK] NumPy Functional Test             : PASSED
  [OK] Pandas Functional Test            : PASSED
  [OK] Matplotlib Sine Wave Test         : PASSED
  [OK] Seaborn 20x20 Heatmap Test        : PASSED
  [OK] SciPy Root Finding Test           : PASSED
  [OK] SymPy Solve & Factorize Test      : PASSED
  [OK] Scikit-learn RandomForest Test    : PASSED
  [OK] Combined Data Science Pipeline    : PASSED
========================================
ALL FUNCTIONAL TESTS PASSED!
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **Shift + Enter** | Run cell and advance |
| **Ctrl + Enter** | Run cell in place |
| **Alt + Enter** | Run cell and insert below |
| **Ctrl + B** | Toggle left navigation sidebar |
| **Ctrl + Shift + P** | Command Palette (`⌘K`) |
| **A** *(outside editor)* | Insert code cell above |
| **B** *(outside editor)* | Insert code cell below |
| **D** *(outside editor)* | Delete selected cell |
| **M** *(outside editor)* | Convert to Markdown |
| **Y** *(outside editor)* | Convert to Python Code |

---

## 📄 License

MIT License — Built for rapid, zero-setup interactive Python computing.
