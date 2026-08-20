"""
QuickLab — Centralized Server Configuration
Defines server parameters, resource limits, execution timeouts, and CORS policies.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

class Settings:
    # Service Information
    APP_NAME: str = "QuickLab Python 3.11 Execution Engine"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("QUICKLAB_ENV", "development")
    
    # Server Binding
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Execution Sandbox & Resource Limits
    EXECUTION_TIMEOUT_SECONDS: int = int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "15"))
    MAX_OUTPUT_BYTES: int = int(os.getenv("MAX_OUTPUT_BYTES", str(5 * 1024 * 1024))) # 5MB limit
    MAX_ACTIVE_SESSIONS: int = int(os.getenv("MAX_ACTIVE_SESSIONS", "200"))
    SESSION_IDLE_TIMEOUT_SECONDS: int = int(os.getenv("SESSION_IDLE_TIMEOUT_SECONDS", "1800")) # 30 min
    
    # File Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SANDBOX_DIR: Path = Path(os.getenv("SANDBOX_DIR", str(BASE_DIR / "sessions"))).resolve()
    DIST_DIR: Path = (BASE_DIR / "dist").resolve()
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]
    
    # Official 7 Supported Libraries
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
