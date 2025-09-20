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

# Run FastAPI with uvicorn
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
