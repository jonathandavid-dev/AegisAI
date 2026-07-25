# Use a clean Python 3.12 slim base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# IMPORTANT: Install PyTorch CPU-only FIRST before other requirements.
# This prevents pip from resolving the CUDA-enabled torch (~1.5GB) pulled
# in by sentence-transformers. CPU-only torch is ~200MB and sufficient for
# embedding and cross-encoder inference in a backend container.
RUN pip install --no-cache-dir \
    torch==2.3.1+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Copy and install remaining dependencies (sentence-transformers will reuse torch above)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and config files
COPY . .

# Expose FastAPI backend default port
EXPOSE 8000

# Start server via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
