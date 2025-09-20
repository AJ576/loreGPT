# Use Python base
FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Install system deps (if FAISS or numpy needs it)
RUN apt-get update && apt-get install -y build-essential

# Copy requirements
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Expose API port
EXPOSE 8000

# Start app (adjust if you use Flask instead of FastAPI)
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
