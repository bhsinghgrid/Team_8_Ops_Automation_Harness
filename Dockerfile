# Use a lightweight Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the working directory
COPY . .

# Set environment variable for Gemini API Key (replace with your actual key during runtime or build)
# It is recommended to pass this at runtime using -e GEMINI_API_KEY="YOUR_KEY"
ENV GEMINI_API_KEY="your_gemini_api_key_here"

# Command to run the pipeline script
# Ensure the path to the script is correct relative to the WORKDIR
CMD ["python", "run_pipeline.py"]
