# ============================================================
# Stage 1: Build Frontend Assets (React + Vite)
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ============================================================
# Stage 2: Production Python 3.11 Execution Environment
# ============================================================
FROM python:3.11-slim-bookworm

LABEL maintainer="QuickLab Team"
LABEL description="QuickLab — Zero-setup Python 3.11 interactive sandbox (NumPy, Pandas, Matplotlib, Seaborn, SciPy, SymPy, Scikit-learn)."

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    DEBIAN_FRONTEND=noninteractive \
    QUICKLAB_ENV=production \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    EXECUTION_TIMEOUT_SECONDS=15

# Install system dependencies
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

# Install standard Python 3.11 scientific & server dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt pytest httpx

# Create isolated sandbox directory
RUN mkdir -p /app/sessions && chown -R quicklab:quicklab /app

# Copy server code and verification scripts
COPY --chown=quicklab:quicklab server /app/server
COPY --chown=quicklab:quicklab scripts /app/scripts
COPY --chown=quicklab:quicklab tests /app/tests

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder --chown=quicklab:quicklab /build/dist /app/dist

# Verify the 7 pre-installed libraries and run test suite during image build
RUN python scripts/test-python-packages.py && pytest tests/ -v

# Switch to non-root user
USER quicklab

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
