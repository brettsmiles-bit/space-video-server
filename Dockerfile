# Use slim Python base
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency list
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Run app (Render sets $PORT automatically)
CMD ["python", "app.py"]
