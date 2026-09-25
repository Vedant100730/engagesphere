FROM python:3.11-slim

# Install system dependencies needed by torch/transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first (layer cache)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project (backend + root __init__ if any)
COPY . .

# Expose the port Render expects
EXPOSE 8000

# Start with uvicorn; Render sets PORT env var automatically
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
