FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-simple.txt .
RUN pip install --no-cache-dir -r requirements-simple.txt

# Copy application code
COPY backend/ ./backend/
COPY ai/ ./ai/
COPY .env .env

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Start command
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]