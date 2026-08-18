"""
QuickLab — Session Manager
Manages isolated in-memory Python session states and ephemeral sandbox storage.
"""

import os
import shutil
import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Tuple
from server.execution import run_code_in_session


class Session:
    def __init__(self, session_id: str, base_sandbox_dir: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_active = time.time()
        self.execution_count = 0
        self.lock = threading.Lock()
        self.sandbox_dir = os.path.join(base_sandbox_dir, session_id)
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.globals_dict: Dict[str, Any] = self._create_clean_globals()

    def _create_clean_globals(self) -> Dict[str, Any]:
        """Creates a clean global execution namespace for the session."""
        g = {
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
            "_": None
        }
        return g

    def reset(self):
        """Restarts the session kernel, wiping all variables and recreating clean namespace."""
        with self.lock:
            self.globals_dict = self._create_clean_globals()
            self.execution_count = 0
            self.last_active = time.time()

    def execute(self, code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
        with self.lock:
            self.last_active = time.time()
            self.execution_count += 1
            outputs, variables = run_code_in_session(
                code=code,
                globals_dict=self.globals_dict,
                session_cwd=self.sandbox_dir
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
        self.base_sandbox_dir = base_sandbox_dir or os.path.abspath("./sessions")
        os.makedirs(self.base_sandbox_dir, exist_ok=True)
        self.sessions: Dict[str, Session] = {}
        self.lock = threading.Lock()

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        with self.lock:
            if not session_id or session_id not in self.sessions:
                sid = session_id or str(uuid.uuid4())
                session = Session(sid, self.base_sandbox_dir)
                self.sessions[sid] = session
                return session
            s = self.sessions[session_id]
            s.last_active = time.time()
            return s

    def get(self, session_id: str) -> Optional[Session]:
        with self.lock:
            return self.sessions.get(session_id)

    def remove(self, session_id: str) -> bool:
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions.pop(session_id)
                session.cleanup()
                return True
            return False

    def list_files(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get(session_id)
        if not session or not os.path.exists(session.sandbox_dir):
            return []
        files = []
        try:
            for fname in os.listdir(session.sandbox_dir):
                fpath = os.path.join(session.sandbox_dir, fname)
                if os.path.isfile(fpath):
                    size = os.path.getsize(fpath)
                    files.append({"name": fname, "size": size, "path": fpath})
        except Exception:
            pass
        return files

    def save_file(self, session_id: str, filename: str, content: bytes) -> str:
        session = self.get_or_create(session_id)
        safe_name = os.path.basename(filename)
        dest_path = os.path.join(session.sandbox_dir, safe_name)
        with open(dest_path, "wb") as f:
            f.write(content)
        return dest_path

    def delete_file(self, session_id: str, filename: str) -> bool:
        session = self.get(session_id)
        if not session:
            return False
        safe_name = os.path.basename(filename)
        fpath = os.path.join(session.sandbox_dir, safe_name)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                return True
            except Exception:
                pass
        return False

    def clean_inactive_sessions(self, max_idle_seconds: int = 1800):
        """Cleans up sessions that have been idle for longer than max_idle_seconds."""
        now = time.time()
        with self.lock:
            to_delete = [
                sid for sid, s in self.sessions.items()
                if now - s.last_active > max_idle_seconds
            ]
            for sid in to_delete:
                s = self.sessions.pop(sid, None)
                if s:
                    s.cleanup()
