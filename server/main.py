"""
QuickLab — Execution API Server
FastAPI backend providing REST & WebSocket endpoints for running Python 3.11 code,
managing temporary sessions, file uploads, kernel controls, real-time streaming,
and secure Gemini AI assistance.
"""

import sys
import os
import time
import platform
import asyncio
import logging
import importlib.metadata
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from server.config import settings
from server.security import (
    enforce_rate_limit,
    validate_session_id,
    validate_filename,
    validate_code_input
)
from server.session_manager import SessionManager
from server.services.gemini import gemini_service

# Configure server logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quicklab")

app = FastAPI(
    title=settings.APP_NAME,
    description="Pre-installed Python 3.11 scientific and ML execution sandbox.",
    version=settings.VERSION
)

# Enable CORS with configurable, non-wildcard production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session manager initialization
session_mgr = SessionManager(base_sandbox_dir=str(settings.SANDBOX_DIR))


class ExecuteRequest(BaseModel):
    code: str = Field(..., max_length=settings.MAX_CODE_SIZE_BYTES)
    session_id: Optional[str] = Field(None, max_length=64)
    timeout: Optional[int] = Field(None, ge=1, le=60)


class RestartRequest(BaseModel):
    session_id: str = Field(..., max_length=64)


class AIExplainRequest(BaseModel):
    code: str = Field(..., max_length=settings.MAX_CODE_SIZE_BYTES)
    context: Optional[str] = Field(None, max_length=1000)


class AIFixErrorRequest(BaseModel):
    code: str = Field(..., max_length=settings.MAX_CODE_SIZE_BYTES)
    error: str = Field(..., max_length=10000)


class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., max_length=2000)


def get_client_ip(request: Request) -> str:
    """Extracts client IP address for rate limiting."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@app.get("/api/health")
def health():
    """Healthcheck returning Python version, platform, engine, and runtime status."""
    return {
        "status": "ok",
        "engine": "QuickLab Python 3.11 Docker Engine",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "total_packages": len(settings.OFFICIAL_PACKAGES),
        "environment": settings.ENVIRONMENT,
        "ai_enabled": gemini_service.is_configured()
    }


@app.get("/api/packages")
def get_packages():
    """Returns actual installed versions of the 7 official QuickLab V1 libraries."""
    result = []
    for pkg in settings.OFFICIAL_PACKAGES:
        pkg_name = pkg["name"]
        ver = "not installed"
        pkg_status = False
        try:
            ver = importlib.metadata.version(pkg_name)
            pkg_status = True
        except Exception:
            mod_alias = {"scikit-learn": "sklearn"}.get(pkg_name, pkg_name)
            try:
                mod = __import__(mod_alias)
                ver = getattr(mod, "__version__", "installed")
                pkg_status = True
            except Exception:
                pass

        result.append({
            "name": pkg_name,
            "category": pkg["category"],
            "description": pkg["desc"],
            "version": ver,
            "installed": pkg_status
        })

    return {
        "python_version": platform.python_version(),
        "packages": result
    }


@app.post("/api/session")
def create_session(request: Request):
    """Creates a new isolated temporary execution session."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_SESSION_PER_MIN, "Session Creation")

    try:
        session = session_mgr.get_or_create()
        return {"session_id": session.session_id, "created_at": session.created_at}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize session.")


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str, request: Request):
    """Destroys an ephemeral session and wipes its sandbox files."""
    sid = validate_session_id(session_id)
    deleted = session_mgr.remove(sid)
    return {"session_id": sid, "deleted": deleted}


@app.post("/api/execute")
def execute_code(req: ExecuteRequest, request: Request):
    """Executes Python code in the requested session and returns structured outputs."""
    client_ip = get_client_ip(request)
    rate_key = f"{client_ip}_{req.session_id or 'default'}"
    enforce_rate_limit(rate_key, settings.RATE_LIMIT_EXECUTE_PER_MIN, "Code Execution")

    validate_code_input(req.code)
    sid = validate_session_id(req.session_id) if req.session_id else None

    try:
        session = session_mgr.get_or_create(sid)
        outputs, variables, exec_count = session.execute(
            code=req.code,
            timeout_seconds=req.timeout
        )
        return {
            "session_id": session.session_id,
            "exec_count": exec_count,
            "outputs": outputs,
            "variables": variables
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during code execution: {e}", exc_info=True)
        return {
            "session_id": req.session_id,
            "exec_count": 0,
            "outputs": [{"kind": "error", "text": "An internal execution error occurred."}],
            "variables": []
        }


@app.post("/api/restart")
def restart_kernel(req: RestartRequest, request: Request):
    """Restarts the session kernel, purging all variables from memory."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_EXECUTE_PER_MIN, "Kernel Restart")

    sid = validate_session_id(req.session_id)
    session = session_mgr.get(sid)
    if not session:
        session = session_mgr.get_or_create(sid)
    session.reset()
    return {
        "session_id": session.session_id,
        "success": True,
        "message": "Kernel restarted. All session variables cleared."
    }


@app.get("/api/variables/{session_id}")
def get_variables(session_id: str):
    """Returns the list of active user variables in the session."""
    sid = validate_session_id(session_id)
    session = session_mgr.get(sid)
    if not session:
        return {"variables": []}
    from server.execution import inspect_variables
    vars_list = inspect_variables(session.globals_dict)
    return {"session_id": sid, "variables": vars_list}


@app.post("/api/files/upload")
async def upload_file(
    request: Request,
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Uploads an allowed data file (.csv, .txt, .json) to the session sandbox."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_UPLOAD_PER_MIN, "File Upload")

    sid = validate_session_id(session_id)
    safe_filename = validate_filename(file.filename)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
        )

    try:
        dest = session_mgr.save_file(sid, safe_filename, content)
        return {
            "session_id": sid,
            "filename": safe_filename,
            "size": len(content),
            "path": safe_filename
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save uploaded file.")


@app.get("/api/files/{session_id}")
def list_session_files(session_id: str):
    """Lists all files stored in the session sandbox."""
    sid = validate_session_id(session_id)
    files = session_mgr.list_files(sid)
    return {"session_id": sid, "files": files}


@app.get("/api/files/{session_id}/{filename:path}")
def download_session_file(session_id: str, filename: str):
    """Downloads a file from the session sandbox."""
    sid = validate_session_id(session_id)
    safe_name = validate_filename(filename)

    session = session_mgr.get(sid)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    
    fpath = os.path.abspath(os.path.join(session.sandbox_dir, safe_name))
    if os.path.commonpath([session.sandbox_dir, fpath]) != session.sandbox_dir or not os.path.exists(fpath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    
    return FileResponse(fpath, filename=safe_name)


@app.delete("/api/files/{session_id}/{filename:path}")
def delete_session_file(session_id: str, filename: str, request: Request):
    """Deletes a file from the session sandbox."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_UPLOAD_PER_MIN, "File Deletion")

    sid = validate_session_id(session_id)
    safe_name = validate_filename(filename)

    deleted = session_mgr.delete_file(sid, safe_name)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or cannot be deleted.")
    return {"session_id": sid, "filename": safe_name, "deleted": True}


# ============================================================
# Gemini AI Assistant Endpoints
# ============================================================

@app.get("/api/ai/status")
def ai_status():
    """Returns whether Gemini AI assistance is configured on the backend."""
    return {"configured": gemini_service.is_configured(), "model": settings.GEMINI_MODEL}


@app.post("/api/ai/explain")
async def ai_explain(req: AIExplainRequest, request: Request):
    """Explains Python code with context on scientific libraries."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_AI_PER_MIN, "AI Explanation")

    validate_code_input(req.code)

    try:
        result = await gemini_service.explain_code(req.code, req.context)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected AI explain error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI assistance service error.")


@app.post("/api/ai/fix-error")
async def ai_fix_error(req: AIFixErrorRequest, request: Request):
    """Diagnoses runtime/syntax errors and proposes corrected Python code."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_AI_PER_MIN, "AI Fix Error")

    validate_code_input(req.code)

    try:
        result = await gemini_service.fix_error(req.code, req.error)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected AI fix error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI assistance service error.")


@app.post("/api/ai/generate")
async def ai_generate(req: AIGenerateRequest, request: Request):
    """Generates runnable Python code from user instructions."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, settings.RATE_LIMIT_AI_PER_MIN, "AI Code Generation")

    try:
        result = await gemini_service.generate_code(req.prompt)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected AI generate error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI assistance service error.")


@app.get("/api/verify")
async def run_verification(request: Request):
    """Runs scripts/test-python-packages.py and returns the verification report."""
    client_ip = get_client_ip(request)
    enforce_rate_limit(client_ip, 10, "Environment Verification")

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
        logger.error(f"Verification error: {e}", exc_info=True)
        return {"exit_code": 1, "success": False, "output": "Failed to run environment verification."}


@app.websocket("/ws/kernel/{session_id}")
async def websocket_kernel(websocket: WebSocket, session_id: str):
    """Real-time streaming WebSocket endpoint with validation and rate limiting."""
    try:
        sid = validate_session_id(session_id)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    session = session_mgr.get_or_create(sid)
    loop = asyncio.get_event_loop()
    last_exec_time = 0.0

    try:
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                await websocket.send_json({"type": "error", "text": "Invalid message format."})
                continue

            msg_type = data.get("type", "execute")
            code = data.get("code", "")

            if msg_type == "restart":
                session.reset()
                await websocket.send_json({"type": "status", "state": "idle", "msg": "Kernel restarted"})
                continue

            # Enforce execution rate limit (at least 0.2s between executions)
            now = time.time()
            if now - last_exec_time < 0.2:
                await websocket.send_json({"type": "error", "text": "Execution frequency limit exceeded."})
                continue
            last_exec_time = now

            if len(code.encode("utf-8")) > settings.MAX_CODE_SIZE_BYTES:
                await websocket.send_json({"type": "error", "text": "Code payload exceeds maximum size limit."})
                continue

            await websocket.send_json({"type": "status", "state": "busy"})

            def stream_callback(item):
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "stream_chunk", "chunk": item}),
                    loop
                )

            outputs, variables, exec_count = session.execute(
                code=code,
                stream_callback=stream_callback
            )
            await websocket.send_json({
                "type": "result",
                "exec_count": exec_count,
                "outputs": outputs,
                "variables": variables
            })
            await websocket.send_json({"type": "status", "state": "idle"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)


# Serve compiled React frontend if dist exists (Production single-container Docker build)
if settings.DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(settings.DIST_DIR / "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API route not found.")
        file_path = settings.DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(settings.DIST_DIR / "index.html")


@app.on_event("startup")
async def startup_event():
    """Starts background periodic cleaner for inactive sessions."""
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)
            session_mgr.clean_inactive_sessions()
    asyncio.create_task(cleanup_loop())
