FROM python:3.11-slim

# Install system dependencies needed for nvidia-smi and process monitoring
RUN apt-get update && apt-get install -y \
    procps \
    grep \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python requirements first for better caching
COPY requirements.txt* ./

# Install Python dependencies
RUN pip install --no-cache-dir flask flask-cors gunicorn

# Copy application files
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Set Python path to ensure modules are found
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Use gunicorn for production
# Using --preload to load the application before forking workers
# Using wsgi:app for better error visibility
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "30", "--preload", "--log-level", "debug", "--capture-output", "--enable-stdio-inheritance", "--chdir", "/app", "wsgi:app"]