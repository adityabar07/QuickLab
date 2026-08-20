"""
QuickLab — Security & Validation Layer
Enforces input validation, path traversal defense, file upload allowlists,
binary inspection, information disclosure prevention, and sliding-window rate limiting.
"""

import re
import os
import time
import json
import threading
from typing import Dict, List, Tuple, Optional
from fastapi import HTTPException, status
from server.config import settings

# Strict session ID regex: 4 to 64 alphanumeric characters, underscores, or hyphens
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{4,64}$")

# Safe filename regex: 1 to 100 characters consisting of letters, digits, dots, underscores, hyphens
SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{1,100}$")

# Disallowed binary executable magic bytes
EXECUTABLE_SIGNATURES = [
    b"\x7fELF",                # Linux ELF binary
    b"MZ",                      # Windows PE / EXE / DLL
    b"\xca\xfe\xba\xbe",        # Java class / Mach-O universal
    b"\xfe\xed\xfa\xce",        # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf",        # Mach-O 64-bit
    b"#!",                      # Unix shebang executable
]


class RateLimiter:
    """Sliding-window in-memory rate limiter per key (IP or Session ID)."""
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def check(self, key: str, limit_per_minute: int) -> Tuple[bool, int]:
        """
        Returns (allowed: bool, retry_after_seconds: int).
        """
        now = time.time()
        window_start = now - 60.0

        with self.lock:
            if key not in self.requests:
                self.requests[key] = [now]
                return True, 0

            # Prune timestamps outside the 1-minute window
            valid_timestamps = [ts for ts in self.requests[key] if ts > window_start]
            self.requests[key] = valid_timestamps

            if len(valid_timestamps) >= limit_per_minute:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(60.0 - (now - oldest)))
                return False, retry_after

            self.requests[key].append(now)
            return True, 0

    def cleanup_old_keys(self):
        """Removes inactive keys to prevent memory leak."""
        now = time.time()
        window_start = now - 120.0
        with self.lock:
            keys_to_remove = [
                k for k, timestamps in self.requests.items()
                if not timestamps or timestamps[-1] < window_start
            ]
            for k in keys_to_remove:
                self.requests.pop(k, None)


rate_limiter = RateLimiter()


def enforce_rate_limit(key: str, limit_per_minute: int, endpoint_name: str = "endpoint"):
    """Raises HTTP 429 if the request rate exceeds limit_per_minute."""
    allowed, retry_after = rate_limiter.check(key, limit_per_minute)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {endpoint_name}. Please retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


def validate_session_id(session_id: Optional[str]) -> str:
    """
    Validates session ID format. Rejects null bytes, path traversal, or malformed strings.
    """
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID is required."
        )

    if "\x00" in session_id or ".." in session_id or "/" in session_id or "\\" in session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID: Path traversal characters and null bytes are disallowed."
        )

    if not SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID: Must be 4-64 alphanumeric characters, underscores, or hyphens."
        )

    return session_id


def validate_code_input(code: Optional[str]) -> str:
    """
    Validates Python code size and characters. Rejects null bytes and oversized payloads.
    """
    if code is None:
        return ""

    if "\x00" in code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code contains invalid null bytes."
        )

    code_bytes = code.encode("utf-8", errors="ignore")
    if len(code_bytes) > settings.MAX_CODE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code payload exceeds maximum permitted size of {settings.MAX_CODE_SIZE_BYTES // 1024} KB."
        )

    return code


def validate_filename(filename: str) -> str:
    """
    Validates filename, ensuring it belongs to the allowed extensions list (.csv, .txt, .json),
    contains no path traversal tokens or null bytes, and matches safe naming patterns.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty."
        )

    if "\x00" in filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains forbidden path traversal or null characters."
        )

    safe_name = os.path.basename(filename).strip()
    if not SAFE_FILENAME_PATTERN.match(safe_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid characters. Use alphanumeric, '.', '_', or '-' only."
        )

    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        allowed = ", ".join(sorted(settings.ALLOWED_FILE_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not allowed. Supported formats: {allowed}"
        )

    return safe_name


def validate_file_content(filename: str, content: bytes) -> bytes:
    """
    Validates uploaded file content against size limits, binary execution headers, and structural integrity.
    """
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file exceeds maximum size limit of {max_mb} MB."
        )

    # Reject known binary executable signatures
    for sig in EXECUTABLE_SIGNATURES:
        if content.startswith(sig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Executable files or binary scripts are strictly prohibited."
            )

    # Check for text/JSON validation
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".json":
        try:
            json.loads(content.decode("utf-8"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON file: file content could not be parsed as valid JSON."
            )
    else:
        # Check that .csv / .txt is valid UTF-8/ASCII text without control null bytes
        if b"\x00" in content[:1024]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Binary files are not allowed for text/csv uploads."
            )

    return content


def sanitize_traceback(tb_str: str) -> str:
    """
    Strips internal server paths, Docker host paths, and library internals from tracebacks,
    ensuring only user cell code line numbers and Python error types are displayed.
    """
    if not tb_str:
        return ""

    lines = tb_str.split("\n")
    sanitized_lines = []
    
    for line in lines:
        # Filter out internal server execution engine file paths
        if "server/execution.py" in line or "server\\execution.py" in line:
            continue
        if "concurrent/futures" in line or "threading.py" in line:
            continue
        if "ast.py" in line:
            continue
        
        # Replace local filesystem path prefixes (e.g. C:\... or /app/...) with clean labels
        clean_line = re.sub(r'File ".*?[\\/]([^\\/]+)"', r'File "<\1>"', line)
        clean_line = re.sub(r'File "<server.*?>"', '', clean_line)
        if clean_line.strip():
            sanitized_lines.append(clean_line)

    return "\n".join(sanitized_lines).strip()
