# QuickLab — Instant Interactive Python Notebook Platform

> **Zero Setup · No Login · No Accounts · Pre-installed Python 3.11 Scientific & AI Environment**

QuickLab is a modern, high-performance browser-based Python notebook and experimentation environment. Users can open the URL, immediately import any standard scientific, machine learning, deep learning, NLP, computer vision, or probabilistic AI library, and execute code in an isolated, secure container sandbox.

---

## ⚡ Key Philosophy: IMPORT → USE → RUN

All officially supported QuickLab libraries are **pre-installed and ready out-of-the-box**. 

Users **never** need to run `pip install` for official libraries:

```python
import numpy as np
import pandas as pd
import scipy
import sympy as sp
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import sklearn
import tensorflow as tf
import torch
import cv2
from PIL import Image
import nltk
import spacy
import transformers
import networkx as nx
import pgmpy
import statsmodels.api as sm
```

---

## 📦 Complete Pre-Installed Library Catalog

QuickLab is built on **Python 3.11** (`python:3.11-slim-bookworm`), providing rock-solid mutual compatibility across all packages:

| Category | Libraries Included | Primary Purpose |
| :--- | :--- | :--- |
| **Core Scientific** | `numpy`, `scipy`, `sympy` | Fast N-D arrays, linear algebra, numerical optimization, symbolic algebra |
| **Data Science & Stats** | `pandas`, `polars`, `statsmodels` | High-performance tabular DataFrames, fast columnar data, OLS/econometric modeling |
| **Data Visualization** | `matplotlib`, `seaborn`, `plotly` | Headless 2D plotting, statistical charts, interactive 3D web visualizations |
| **Machine Learning** | `scikit-learn` | Regression, classification, clustering, dimensionality reduction, pipelines |
| **Deep Learning** | `tensorflow-cpu`, `keras`, `torch`, `torchvision`, `torchaudio` | Neural networks, CPU-optimized tensor math, autograd, vision/audio models |
| **Computer Vision** | `opencv-python-headless`, `pillow`, `imageio` | Image processing, spatial filtering, feature extraction, format conversion |
| **NLP & AI** | `nltk`, `spacy`, `transformers`, `sentence-transformers` | Tokenization, POS tagging, NER, transformer models, dense vector embeddings |
| **Probabilistic AI** | `pgmpy` | Bayesian networks, Markov models, probabilistic graphical inference |
| **Graph & Networks** | `networkx` | Graph traversal, shortest path, centrality, network flow algorithms |
| **Spreadsheets & Files** | `openpyxl`, `xlsxwriter`, `h5py` | Read/write Excel `.xlsx` spreadsheets, HDF5 binary data access |
| **Web & Networking** | `requests`, `beautifulsoup4` | HTTP requests, HTML/XML parsing, web data extraction |
| **Notebook Engine** | `ipython`, `ipykernel`, `jupyter-client` | Interactive execution, AST evaluation, rich object formatting |
| **Utilities** | `tqdm`, `joblib`, `pydantic`, `python-dotenv`, `pyyaml` | Progress bars, parallel jobs, data validation, environment settings |

---

## 🚀 Quick Start with Docker

QuickLab uses Docker Compose to run the isolated Python execution backend and web frontend.

### 1. Clone & Build

```bash
git clone https://github.com/adityabar07/QuickLab.git
cd QuickLab

# Build and start all services
docker compose up --build
```

### 2. Access the Application

- **Web Application**: [http://localhost:5173](http://localhost:5173) (or [http://localhost:8000](http://localhost:8000))
- **Backend API**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Automated Package Verification Suite

QuickLab includes an automated verification script that imports every package and runs functional unit tests:

```bash
# Run verification inside Docker container or local Python environment
python scripts/test-python-packages.py
```

### Verification Checks:
```text
======================================================================
  QUICKLAB — PYTHON EXECUTION ENVIRONMENT VERIFICATION
  Python Version: 3.11.x
======================================================================

--- [1/2] IMPORTING OFFICIAL QUICKLAB LIBRARIES ---
  ✓ numpy                    : v1.26.4 (12.4ms)
  ✓ pandas                   : v2.2.2 (18.1ms)
  ✓ scipy                    : v1.13.0 (22.5ms)
  ✓ sympy                    : v1.12.1 (35.2ms)
  ✓ matplotlib               : v3.8.4 (14.6ms)
  ✓ seaborn                  : v0.13.2 (28.3ms)
  ✓ plotly                   : v5.22.0 (15.2ms)
  ✓ scikit-learn             : v1.4.2 (31.8ms)
  ✓ tensorflow               : v2.16.1 (120.4ms)
  ✓ torch                    : v2.3.0 (45.1ms)
  ✓ opencv-python            : v4.9.0.80 (24.3ms)
  ✓ pgmpy                    : v0.1.25 (19.8ms)
  ✓ networkx                 : v3.3 (8.2ms)
  ...

--- [2/2] RUNNING FUNCTIONAL UNIT TESTS ---
  ✓ NumPy (Arrays & Linear Algebra)                : OK (0.8ms)
  ✓ Pandas (DataFrames & HTML Export)              : OK (2.1ms)
  ✓ SciPy (Numerical Optimization)                 : OK (1.4ms)
  ✓ SymPy (Symbolic Equations)                     : OK (3.6ms)
  ✓ Matplotlib (Headless PNG Render)               : OK (18.2ms)
  ✓ Plotly (Interactive JSON/HTML Export)          : OK (4.1ms)
  ✓ Scikit-learn (ML Model Fit & Predict)          : OK (2.9ms)
  ✓ PyTorch (Tensors & Autograd)                   : OK (3.2ms)
  ✓ TensorFlow (Tensor Math)                       : OK (5.4ms)
  ✓ OpenCV & Pillow (Image Transforms)             : OK (2.0ms)
  ✓ NLP (NLTK Tokenize & spaCy Processing)         : OK (4.8ms)
  ✓ pgmpy (Bayesian Network Modeling)              : OK (3.1ms)
  ✓ NetworkX (Graph Algorithms & Shortest Path)    : OK (1.2ms)
  ...
======================================================================
  ALL TESTS PASSED SUCCESSFULLY!
======================================================================
```

---

## 🔒 Security & Sandbox Isolation Architecture

```text
Browser Client
     │
     ▼ (HTTP / WebSocket)
QuickLab Frontend (Vite / React)
     │
     ▼ (REST /api/execute)
FastAPI Execution Server
     │
     ▼ (Isolated Ephemeral Session)
Temporary Sandbox (Non-Root User: UID 1000)
     │
     ├── In-Memory Namespace (Variables, Ast Execution)
     ├── Ephemeral Temp Directory (/sandbox/<session_id>)
     └── Isolated `!pip install` Sandbox
```

1. **Non-Root Execution**: Runs strictly under unprivileged user `quicklab` (`UID 1000`).
2. **Filesystem Isolation**: User files exist only within ephemeral `/sandbox/<session-id>` directory.
3. **No Docker Socket Access**: `/var/run/docker.sock` is never exposed.
4. **Temporary Session Model**: When the user restarts the kernel or closes the session, all memory variables, uploaded files, and temporary packages are purged.
5. **Optional Ephemeral Pip**: Users can install experimental packages using `!pip install <pkg>` without modifying the base image or affecting other users.

---

## 🌐 Local Area Network (LAN) Setup

QuickLab is designed to be accessible across any device on your local WiFi or office network:

1. Find your host machine's local IP address:
   - **Windows**: `ipconfig` (e.g. `192.168.1.105`)
   - **Linux / macOS**: `ip a` or `ifconfig`
2. Start QuickLab with network binding:
   ```bash
   npm run dev -- --host 0.0.0.0
   ```
3. Open on any phone, tablet, or laptop on the same network:
   `http://192.168.1.105:5173`

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **Shift + Enter** | Execute current cell and advance to next cell |
| **Ctrl + Enter** | Execute current cell in place |
| **Alt + Enter** | Execute current cell and insert a new code cell below |
| **Ctrl + B** / **Cmd + B** | Toggle left navigation sidebar |
| **Ctrl + Shift + P** | Open Command Palette (`⌘K`) |
| **A** *(outside editor)* | Insert code cell above |
| **B** *(outside editor)* | Insert code cell below |
| **D** *(outside editor)* | Delete selected cell |
| **M** *(outside editor)* | Convert cell to Markdown |
| **Y** *(outside editor)* | Convert cell to Python Code |

---

## 📄 License

MIT License — Built for rapid, zero-setup Python experimentation.
