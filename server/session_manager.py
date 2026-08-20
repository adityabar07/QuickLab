"""
QuickLab — Session Manager
Manages isolated in-memory Python session states, scratchpad workspaces, and lifecycle cleanup.
"""

import os
import shutil
import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Tuple
from server.config import settings
from server.security import (
    validate_session_id,
    validate_filename,
    validate_file_content
)
from server.execution import run_code_in_session


class Session:
    def __init__(self, session_id: str, base_sandbox_dir: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_active = time.time()
        self.execution_count = 0
        self.lock = threading.Lock()
        
        # Strictly isolate sandbox directory
        self.sandbox_dir = os.path.abspath(os.path.join(base_sandbox_dir, session_id))
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.globals_dict: Dict[str, Any] = self._create_clean_globals()

    def _create_clean_globals(self) -> Dict[str, Any]:
        """Creates a clean global execution namespace for the session."""
        return {
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
            "_": None
        }

    def reset(self):
        """Restarts the session kernel, wiping all variables and recreating clean namespace."""
        with self.lock:
            self.globals_dict = self._create_clean_globals()
            self.execution_count = 0
            self.last_active = time.time()

    def execute(
        self,
        code: str,
        timeout_seconds: Optional[int] = None,
        stream_callback=None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
        with self.lock:
            self.last_active = time.time()
            self.execution_count += 1
            outputs, variables = run_code_in_session(
                code=code,
                globals_dict=self.globals_dict,
                session_cwd=self.sandbox_dir,
                timeout_seconds=timeout_seconds or settings.EXECUTION_TIMEOUT_SECONDS,
                stream_callback=stream_callback
            )
            return outputs, variables, self.execution_count

    def cleanup(self):
        """Destroys the session and removes its sandbox directory."""
        try:
            if os.path.exists(self.sandbox_dir):
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
        except Exception:
            pass


class SessionManager:
    def __init__(self, base_sandbox_dir: Optional[str] = None):
        self.base_sandbox_dir = os.path.abspath(base_sandbox_dir or str(settings.SANDBOX_DIR))
        os.makedirs(self.base_sandbox_dir, exist_ok=True)
        self.sessions: Dict[str, Session] = {}
        self.lock = threading.Lock()

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        sid = validate_session_id(session_id) if session_id else str(uuid.uuid4())
        
        with self.lock:
            if len(self.sessions) >= settings.MAX_ACTIVE_SESSIONS:
                self._purge_oldest_idle()

            if sid not in self.sessions:
                session = Session(sid, self.base_sandbox_dir)
                self.sessions[sid] = session
                return session
            s = self.sessions[sid]
            s.last_active = time.time()
            return s

    def get(self, session_id: str) -> Optional[Session]:
        sid = validate_session_id(session_id)
        with self.lock:
            return self.sessions.get(sid)

    def remove(self, session_id: str) -> bool:
        sid = validate_session_id(session_id)
        with self.lock:
            if sid in self.sessions:
                session = self.sessions.pop(sid)
                session.cleanup()
                return True
            return False

    def list_files(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get(session_id)
        if not session or not os.path.exists(session.sandbox_dir):
            return []
        files = []
        try:
            for fname in sorted(os.listdir(session.sandbox_dir)):
                fpath = os.path.join(session.sandbox_dir, fname)
                if os.path.isfile(fpath):
                    size = os.path.getsize(fpath)
                    files.append({"name": fname, "size": size, "path": fpath})
        except Exception:
            pass
        return files

    def save_file(self, session_id: str, filename: str, content: bytes) -> str:
        session = self.get_or_create(session_id)
        safe_name = validate_filename(filename)
        valid_content = validate_file_content(safe_name, content)
        
        dest_path = os.path.abspath(os.path.join(session.sandbox_dir, safe_name))
        
        # Verify strict sandbox path confinement
        if os.path.commonpath([session.sandbox_dir, dest_path]) != session.sandbox_dir:
            raise ValueError("Path traversal attempt detected.")

        with open(dest_path, "wb") as f:
            f.write(valid_content)

        # Set non-executable permissions (rw-r--r--)
        try:
            os.chmod(dest_path, 0o644)
        except Exception:
            pass

        return dest_path

    def delete_file(self, session_id: str, filename: str) -> bool:
        session = self.get(session_id)
        if not session:
            return False
        safe_name = validate_filename(filename)
        fpath = os.path.abspath(os.path.join(session.sandbox_dir, safe_name))
        
        if os.path.commonpath([session.sandbox_dir, fpath]) == session.sandbox_dir and os.path.exists(fpath):
            try:
                os.remove(fpath)
                return True
            except Exception:
                pass
        return False

    def _purge_oldest_idle(self):
        """Drops the oldest idle session when capacity is reached."""
        if not self.sessions:
            return
        oldest_sid = min(self.sessions.keys(), key=lambda k: self.sessions[k].last_active)
        s = self.sessions.pop(oldest_sid, None)
        if s:
            s.cleanup()

    def clean_inactive_sessions(self, max_idle_seconds: Optional[int] = None):
        """Cleans up sessions that have been idle longer than max_idle_seconds."""
        idle_limit = max_idle_seconds or settings.SESSION_IDLE_TIMEOUT_SECONDS
        now = time.time()
        with self.lock:
            to_delete = [
                sid for sid, s in self.sessions.items()
                if now - s.last_active > idle_limit
            ]
            for sid in to_delete:
                s = self.sessions.pop(sid, None)
                if s:
                    s.cleanup()
