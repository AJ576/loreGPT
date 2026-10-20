# Stage 1: lightweight Python
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Limit thread allocations to save memory in container
ENV OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    TORCH_NUM_THREADS=1

# Install CPU-only PyTorch first (avoids heavy CUDA libraries)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model at build time so it does not spike RAM or download during runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY src ./src
COPY data/index ./data/index

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn (single worker to stay well below 512MB RAM)
CMD ["sh", "-c", "uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
