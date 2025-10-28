FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite storage
RUN mkdir -p /app/data

# Set default environment variables for Railway
ENV HOST=0.0.0.0
ENV PORT=8000
ENV STORAGE_DIR=/app/data

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Run the application with uvicorn
# Railway will provide $PORT environment variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
