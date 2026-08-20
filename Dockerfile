# ============================================================
# QuickLab V1 — Python 3.11 Execution Environment
# ============================================================
FROM python:3.11-slim-bookworm

# Label metadata
LABEL maintainer="QuickLab Team"
LABEL description="QuickLab V1 — Pre-installed scientific & ML environment (NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, Scikit-learn)."

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    DEBIAN_FRONTEND=noninteractive \
    QUICKLAB_ENV=production \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -g 1000 quicklab && \
    useradd -u 1000 -g quicklab -m -s /bin/bash quicklab

WORKDIR /app

# Upgrade pip and install wheel tooling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install the 7 core libraries
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create temporary sandbox directories for session isolation
RUN mkdir -p /app/sessions /sandbox && \
    chown -R quicklab:quicklab /app /sandbox

# Copy server codebase and verification scripts
COPY --chown=quicklab:quicklab server /app/server
COPY --chown=quicklab:quicklab scripts /app/scripts

# Verify all 7 official QuickLab V1 libraries during build time (fails build if any library is missing)
RUN python -c "\
import numpy; \
import pandas; \
import matplotlib; \
import seaborn; \
import scipy; \
import sympy; \
import sklearn; \
print('========================================'); \
print('ALL 7 QUICKLAB V1 LIBRARIES VERIFIED'); \
print('========================================')\
"

# Switch to non-root user
USER quicklab

# Expose backend API port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start execution server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
