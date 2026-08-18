# ============================================================
# QuickLab — Complete Python 3.11 Execution Environment
# ============================================================
FROM python:3.11-slim-bookworm

# Label metadata
LABEL maintainer="QuickLab Team"
LABEL description="Complete pre-installed Python data-science, ML, DL, NLP, and AI execution sandbox."

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
    libglib2.0-0 \
    curl \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -g 1000 quicklab && \
    useradd -u 1000 -g quicklab -m -s /bin/bash quicklab

WORKDIR /app

# Copy requirements and install CPU PyTorch & all dependencies
COPY requirements.txt /app/requirements.txt

# Install PyTorch CPU wheels first for optimal image size & speed, then all requirements
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download core NLTK data into shared system directory
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt stopwords wordnet averaged_perceptron_tagger_eng

# Create temporary sandbox directories for session isolation
RUN mkdir -p /app/sessions /sandbox && \
    chown -R quicklab:quicklab /app /sandbox /usr/local/share/nltk_data

# Copy server codebase and verification scripts
COPY --chown=quicklab:quicklab server /app/server
COPY --chown=quicklab:quicklab scripts /app/scripts

# Switch to non-root user
USER quicklab

# Expose backend API port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start execution server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
