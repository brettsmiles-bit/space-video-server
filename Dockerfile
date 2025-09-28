# Use slim Python base image
FROM python:3.10-slim

# Install ffmpeg and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose Render's port (optional, for clarity)
EXPOSE 10000

# Run the Flask app (Render sets $PORT automatically)
CMD ["python", "app.py"]
