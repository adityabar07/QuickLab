"""
QuickLab V1 — Execution API Server
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
    title="QuickLab Python 3.11 Execution Engine",
    description="Pre-installed Python 3.11 scientific and ML execution sandbox (NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, Scikit-learn).",
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

# Official QuickLab V1 Package Catalog (Exactly 7 Core Libraries)
OFFICIAL_PACKAGES = [
    {"name": "numpy", "category": "Core Scientific", "desc": "N-dimensional arrays & numerical operations"},
    {"name": "pandas", "category": "Data Science", "desc": "Tabular DataFrames & structured data analysis"},
    {"name": "matplotlib", "category": "Visualization", "desc": "2D plotting and graphical figures"},
    {"name": "seaborn", "category": "Visualization", "desc": "Statistical charts, distributions & heatmaps"},
    {"name": "scipy", "category": "Scientific Computing", "desc": "Numerical optimization, linear algebra & science routines"},
    {"name": "sympy", "category": "Symbolic Mathematics", "desc": "Symbolic algebra, equations & calculus"},
    {"name": "scikit-learn", "category": "Machine Learning", "desc": "Classical machine learning models, classifiers & pipelines"}
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
        "engine": "docker",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "total_packages": len(OFFICIAL_PACKAGES)
    }


@app.get("/api/packages")
def get_packages():
    """Returns actual installed versions of the 7 official QuickLab V1 libraries."""
    result = []
    for pkg in OFFICIAL_PACKAGES:
        pkg_name = pkg["name"]
        ver = "not installed"
        status = False
        try:
            ver = importlib.metadata.version(pkg_name)
            status = True
        except Exception:
            mod_alias = {"scikit-learn": "sklearn"}.get(pkg_name, pkg_name)
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
    """Uploads a data file (CSV, TXT, JSON) to the session sandbox."""
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
            timeout=60
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
