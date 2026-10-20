# Stage 1: lightweight Python
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy only needed files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY data/index ./data/index

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn (binds to Render's dynamic $PORT or 8000 by default)
CMD ["sh", "-c", "uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
