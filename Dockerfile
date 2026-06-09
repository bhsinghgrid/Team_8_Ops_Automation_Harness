# Dockerfile for Magellan Runbook Execution (Worker & Backend)
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
# We use the requirements from the backend project as the base
COPY magellan_signal_ingestion_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for Temporal and Evaluation
RUN pip install --no-cache-dir \
    temporalio \
    elasticsearch \
    pydantic-settings \
    python-dotenv \
    google-genai \
    httpx \
    ranx \
    prometheus_client

# Copy the entire project structure
COPY . .

# Set PYTHONPATH to include the root directory
ENV PYTHONPATH="/app"

# Expose ports for Prometheus (8001) and Backend (8000)
EXPOSE 8000 8001

# Default command is overridden in docker-compose
CMD ["python", "magellan_signal_ingestion_backend/app/main.py"]
