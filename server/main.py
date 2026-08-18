"""
QuickLab — Execution API Server
FastAPI backend providing REST & WebSocket endpoints for running Python 3.11 code,
managing temporary sessions, file uploads, kernel controls, and package introspection.
"""

import sys
import os
import platform
import asyncio
import importlib.metadata
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from server.session_manager import SessionManager

app = FastAPI(
    title="QuickLab Python Execution Engine",
    description="Pre-installed Python 3.11 scientific and ML execution sandbox.",
    version="1.0.0"
)

# Enable CORS for frontend and LAN access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session manager initialization
SANDBOX_DIR = os.getenv("SANDBOX_DIR", os.path.abspath("./sessions"))
session_mgr = SessionManager(base_sandbox_dir=SANDBOX_DIR)

# Official QuickLab Package Catalog
OFFICIAL_PACKAGES = [
    {"name": "numpy", "category": "Core Scientific", "desc": "N-dimensional array operations & linear algebra"},
    {"name": "scipy", "category": "Core Scientific", "desc": "Scientific algorithms & numerical optimization"},
    {"name": "sympy", "category": "Core Scientific", "desc": "Symbolic mathematics and algebra"},
    {"name": "pandas", "category": "Data Science", "desc": "High-performance tabular data structures"},
    {"name": "polars", "category": "Data Science", "desc": "Blazing-fast columnar DataFrame library"},
    {"name": "statsmodels", "category": "Statistics", "desc": "Statistical modeling and econometrics"},
    {"name": "matplotlib", "category": "Visualization", "desc": "2D plotting and figures"},
    {"name": "seaborn", "category": "Visualization", "desc": "Statistical data visualization"},
    {"name": "plotly", "category": "Visualization", "desc": "Interactive web-based charting"},
    {"name": "scikit-learn", "category": "Machine Learning", "desc": "Classical ML models & preprocessing"},
    {"name": "tensorflow", "category": "Deep Learning", "desc": "Neural networks & tensor computations"},
    {"name": "keras", "category": "Deep Learning", "desc": "High-level deep learning API"},
    {"name": "torch", "category": "Deep Learning", "desc": "PyTorch tensor computation & autograd"},
    {"name": "torchvision", "category": "Deep Learning", "desc": "Computer vision models for PyTorch"},
    {"name": "torchaudio", "category": "Deep Learning", "desc": "Audio processing models for PyTorch"},
    {"name": "opencv-python", "category": "Computer Vision", "desc": "Computer vision & image processing"},
    {"name": "pillow", "category": "Computer Vision", "desc": "Image manipulation library (PIL)"},
    {"name": "imageio", "category": "Computer Vision", "desc": "Image read/write utility"},
    {"name": "nltk", "category": "Natural Language Processing", "desc": "Natural Language Toolkit & tokenizers"},
    {"name": "spacy", "category": "Natural Language Processing", "desc": "Industrial-strength NLP pipelines"},
    {"name": "transformers", "category": "Natural Language Processing", "desc": "HuggingFace transformer models"},
    {"name": "sentence-transformers", "category": "Natural Language Processing", "desc": "Dense vector sentence embeddings"},
    {"name": "pgmpy", "category": "Probabilistic AI", "desc": "Bayesian networks & probabilistic graphical models"},
    {"name": "networkx", "category": "Graph Algorithms", "desc": "Network and graph analysis algorithms"},
    {"name": "openpyxl", "category": "Spreadsheets", "desc": "Read/write Excel .xlsx spreadsheets"},
    {"name": "xlsxwriter", "category": "Spreadsheets", "desc": "Create Excel charts and formatted sheets"},
    {"name": "h5py", "category": "File Processing", "desc": "HDF5 binary data format interface"},
    {"name": "requests", "category": "Web & Networking", "desc": "HTTP client library"},
    {"name": "beautifulsoup4", "category": "Web & Networking", "desc": "HTML and XML parser"},
    {"name": "ipython", "category": "Notebook Engine", "desc": "Interactive Python execution tools"},
    {"name": "tqdm", "category": "Utilities", "desc": "Extensible progress bars"},
    {"name": "joblib", "category": "Utilities", "desc": "Parallel computation & model persistence"},
    {"name": "pydantic", "category": "Utilities", "desc": "Data validation and settings management"}
]


class ExecuteRequest(BaseModel):
    code: str
    session_id: Optional[str] = None


class RestartRequest(BaseModel):
    session_id: str


@app.get("/api/health")
def health():
    """Healthcheck returning Python version, platform, and runtime status."""
    return {
        "status": "ok",
        "engine": "QuickLab Python 3.11 Docker Engine",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "total_packages": len(OFFICIAL_PACKAGES)
    }


@app.get("/api/packages")
def get_packages():
    """Returns actual installed versions of all official QuickLab libraries."""
    result = []
    for pkg in OFFICIAL_PACKAGES:
        pkg_name = pkg["name"]
        ver = "not installed"
        status = False
        try:
            ver = importlib.metadata.version(pkg_name)
            status = True
        except Exception:
            # Try module import directly
            mod_alias = {
                "scikit-learn": "sklearn",
                "opencv-python": "cv2",
                "pillow": "PIL",
                "beautifulsoup4": "bs4",
                "sentence-transformers": "sentence_transformers"
            }.get(pkg_name, pkg_name)
            try:
                mod = __import__(mod_alias)
                ver = getattr(mod, "__version__", "installed")
                status = True
            except Exception:
                pass

        result.append({
            "name": pkg_name,
            "category": pkg["category"],
            "description": pkg["desc"],
            "version": ver,
            "installed": status
        })

    return {
        "python_version": platform.python_version(),
        "packages": result
    }


@app.post("/api/session")
def create_session():
    """Creates a new isolated temporary execution session."""
    session = session_mgr.get_or_create()
    return {"session_id": session.session_id, "created_at": session.created_at}


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    """Destroys an ephemeral session and wipes its sandbox files."""
    deleted = session_mgr.remove(session_id)
    return {"session_id": session_id, "deleted": deleted}


@app.post("/api/execute")
def execute_code(req: ExecuteRequest):
    """Executes Python code in the requested session and returns structured outputs."""
    session = session_mgr.get_or_create(req.session_id)
    outputs, variables, exec_count = session.execute(req.code)
    return {
        "session_id": session.session_id,
        "exec_count": exec_count,
        "outputs": outputs,
        "variables": variables
    }


@app.post("/api/restart")
def restart_kernel(req: RestartRequest):
    """Restarts the session kernel, purging all variables from memory."""
    session = session_mgr.get(req.session_id)
    if not session:
        session = session_mgr.get_or_create(req.session_id)
    session.reset()
    return {
        "session_id": session.session_id,
        "success": True,
        "message": "Kernel restarted. All session variables cleared."
    }


@app.get("/api/variables/{session_id}")
def get_variables(session_id: str):
    """Returns the list of active user variables in the session."""
    session = session_mgr.get(session_id)
    if not session:
        return {"variables": []}
    from server.execution import inspect_variables
    vars_list = inspect_variables(session.globals_dict)
    return {"session_id": session_id, "variables": vars_list}


@app.post("/api/files/upload")
async def upload_file(session_id: str = Form(...), file: UploadFile = File(...)):
    """Uploads a data file (CSV, JSON, XLSX, TXT, images) to the session sandbox."""
    content = await file.read()
    dest = session_mgr.save_file(session_id, file.filename, content)
    return {
        "session_id": session_id,
        "filename": file.filename,
        "size": len(content),
        "path": dest
    }


@app.get("/api/files/{session_id}")
def list_session_files(session_id: str):
    """Lists all files stored in the session sandbox."""
    files = session_mgr.list_files(session_id)
    return {"session_id": session_id, "files": files}


@app.get("/api/files/{session_id}/{filename}")
def download_session_file(session_id: str, filename: str):
    """Downloads a generated or uploaded file from the session sandbox."""
    session = session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    safe_name = os.path.basename(filename)
    fpath = os.path.join(session.sandbox_dir, safe_name)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(fpath, filename=safe_name)


@app.delete("/api/files/{session_id}/{filename}")
def delete_session_file(session_id: str, filename: str):
    """Deletes a file from the session sandbox."""
    deleted = session_mgr.delete_file(session_id, filename)
    return {"session_id": session_id, "filename": filename, "deleted": deleted}


@app.get("/api/verify")
async def run_verification():
    """Runs scripts/test-python-packages.py and returns the verification report."""
    import subprocess
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "test-python-packages.py"))
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        return {
            "exit_code": proc.returncode,
            "success": proc.returncode == 0,
            "output": proc.stdout + "\n" + proc.stderr
        }
    except Exception as e:
        return {"exit_code": 1, "success": False, "output": str(e)}


@app.websocket("/ws/kernel/{session_id}")
async def websocket_kernel(websocket: WebSocket, session_id: str):
    """Real-time streaming WebSocket endpoint for interactive execution."""
    await websocket.accept()
    session = session_mgr.get_or_create(session_id)
    try:
        while True:
            data = await websocket.receive_json()
            code = data.get("code", "")
            msg_type = data.get("type", "execute")

            if msg_type == "restart":
                session.reset()
                await websocket.send_json({"type": "status", "state": "idle", "msg": "Kernel restarted"})
                continue

            await websocket.send_json({"type": "status", "state": "busy"})
            outputs, variables, exec_count = session.execute(code)
            await websocket.send_json({
                "type": "result",
                "exec_count": exec_count,
                "outputs": outputs,
                "variables": variables
            })
            await websocket.send_json({"type": "status", "state": "idle"})
    except WebSocketDisconnect:
        pass


@app.on_event("startup")
async def startup_event():
    """Starts background periodic cleaner for inactive sessions."""
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)
            session_mgr.clean_inactive_sessions(max_idle_seconds=1800)
    asyncio.create_task(cleanup_loop())
