# Stage 1: Base image with Python and essential build tools
FROM python:3.11-slim-bookworm

# Set environment variables for non-interactive setup
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies, including those required for gcloud and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    gnupg \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install the Google Cloud SDK (gcloud)
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-sdk

# Install the Temporal CLI (tcld)
RUN curl -sSf https://temporal.download/cli.sh | sh \
    && mv /root/.temporalio/bin/temporal /usr/local/bin/tcld

# Set the working directory in the container
WORKDIR /app

# Copy and install Python dependencies
# This is done in a separate step to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install shadow_agent in editable mode from the mounted volume
# Temporarily change WORKDIR to install shadow_agent
WORKDIR /app/shadow_agent_repo
RUN ls -la .
RUN cat setup.py
RUN pip install --no-cache-dir -e .
# Change WORKDIR back to /app for the rest of the application
WORKDIR /app

# Copy the entire project source code into the container
COPY . .

# Copy the startup script and make it executable
COPY start.sh .
RUN chmod +x ./start.sh

# Expose the port the FastAPI server will run on
EXPOSE 8000

# Set the command to run the startup script
CMD ["./start.sh"]
