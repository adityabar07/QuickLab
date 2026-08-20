#!/usr/bin/env python3
"""
QuickLab Repository Secret & Credential Scanner
Scans tracked files for accidental credentials, secrets, private keys, or API tokens.
"""

import os
import re
import sys
from pathlib import Path

# High-risk secret detection patterns
SECRET_PATTERNS = [
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI / Generic Secret Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
    (r"-----BEGIN (?:RSA )?PRIVATE KEY-----", "Private Key Block"),
    (r"-----BEGIN CERTIFICATE-----", "Certificate Block"),
    (r'"type":\s*"service_account"', "GCP Service Account JSON"),
    (r'"private_key":\s*"-----BEGIN', "Service Account Private Key"),
]

IGNORED_DIRS = {".git", "node_modules", ".venv", "venv", "env", "dist", "build", "__pycache__", ".pytest_cache", "sessions"}
IGNORED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".ico", ".webp", ".svg", ".map", ".pyc", ".lock", ".woff", ".woff2", ".ttf"}
IGNORED_FILES = {".env", "security_check.py"}


def scan_file(filepath: Path) -> list:
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for pattern, desc in SECRET_PATTERNS:
            matches = re.finditer(pattern, content)
            for m in matches:
                line_no = content.count("\n", 0, m.start()) + 1
                violations.append((line_no, desc))
    except Exception:
        pass
    return violations


def run_security_scan(root_dir: Path) -> int:
    print(f"[*] Starting QuickLab Security Audit in: {root_dir}")
    total_scanned = 0
    issues = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if file in IGNORED_FILES or any(file.endswith(ext) for ext in IGNORED_EXTENSIONS):
                continue
            
            filepath = Path(root) / file
            rel_path = filepath.relative_to(root_dir)
            total_scanned += 1

            file_violations = scan_file(filepath)
            if file_violations:
                for line_no, desc in file_violations:
                    issues.append((str(rel_path), line_no, desc))

    print(f"[*] Scanned {total_scanned} files across repository.")

    if issues:
        print("\n[!] CRITICAL: Potential security issue(s) found:")
        for path, line, desc in issues:
            print(f"    - {path}:{line} -> {desc}")
        print("\n[X] SECURITY AUDIT FAILED. Please sanitize repository before public release.\n")
        return 1
    else:
        print("[+] SUCCESS: No hardcoded API keys, private keys, or credentials found.")
        print("[+] QuickLab repository is clean.\n")
        return 0


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    sys.exit(run_security_scan(base_dir))
