# -----------------------------
# Space Video Server - Dockerfile
# -----------------------------

# Base image
FROM python:3.10-slim

# Prevent interactive debconf
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (ffmpeg needed for moviepy)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (Render will override with $PORT)
EXPOSE 5000

# Run Flask with correct host/port
CMD ["python", "app.py"]
