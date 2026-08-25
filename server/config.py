"""
QuickLab — Centralized Server Configuration & Security Policies
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Set

class Settings:
    # Service Information
    APP_NAME: str = "QuickLab Python 3.11 Execution Engine"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("QUICKLAB_ENV", "development")
    
    # Server Binding
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration (Configurable via environment for deployed Vercel domain & local dev)
    raw_cors = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:8000"
    )
    CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]
    
    # Execution Sandbox & Resource Limits
    EXECUTION_TIMEOUT_SECONDS: int = int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "15"))
    MAX_OUTPUT_BYTES: int = int(os.getenv("MAX_OUTPUT_BYTES", str(5 * 1024 * 1024))) # 5MB limit
    MAX_CODE_SIZE_BYTES: int = int(os.getenv("MAX_CODE_SIZE_BYTES", str(64 * 1024))) # 64KB max code
    MAX_ACTIVE_SESSIONS: int = int(os.getenv("MAX_ACTIVE_SESSIONS", "200"))
    SESSION_IDLE_TIMEOUT_SECONDS: int = int(os.getenv("SESSION_IDLE_TIMEOUT_SECONDS", "1800")) # 30 min
    
    # File Upload Security Constraints
    ALLOWED_FILE_EXTENSIONS: Set[str] = {".csv", ".txt", ".json"}
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024))) # 5MB max upload
    
    # Rate Limiting Policies (requests per minute)
    RATE_LIMIT_EXECUTE_PER_MIN: int = int(os.getenv("RATE_LIMIT_EXECUTE_PER_MIN", "60"))
    RATE_LIMIT_UPLOAD_PER_MIN: int = int(os.getenv("RATE_LIMIT_UPLOAD_PER_MIN", "20"))
    RATE_LIMIT_SESSION_PER_MIN: int = int(os.getenv("RATE_LIMIT_SESSION_PER_MIN", "30"))
    RATE_LIMIT_GLOBAL_PER_MIN: int = int(os.getenv("RATE_LIMIT_GLOBAL_PER_MIN", "180"))
    
    # File Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SANDBOX_DIR: Path = Path(os.getenv("SANDBOX_DIR", str(BASE_DIR / "sessions"))).resolve()
    DIST_DIR: Path = (BASE_DIR / "dist").resolve()
    
    # Official 7 Supported User Libraries (Strictly V1 standard)
    OFFICIAL_PACKAGES: List[Dict[str, Any]] = [
        {"name": "numpy", "category": "Core Scientific", "desc": "N-dimensional arrays & numerical operations"},
        {"name": "pandas", "category": "Data Science", "desc": "Tabular DataFrames & structured data analysis"},
        {"name": "matplotlib", "category": "Visualization", "desc": "2D plotting and graphical figures"},
        {"name": "seaborn", "category": "Visualization", "desc": "Statistical charts, distributions & heatmaps"},
        {"name": "scipy", "category": "Scientific Computing", "desc": "Numerical optimization, linear algebra & science routines"},
        {"name": "sympy", "category": "Symbolic Mathematics", "desc": "Symbolic algebra, equations & calculus"},
        {"name": "scikit-learn", "category": "Machine Learning", "desc": "Classical machine learning models, classifiers & pipelines"}
    ]

settings = Settings()

# Ensure sandbox directory exists
try:
    settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
