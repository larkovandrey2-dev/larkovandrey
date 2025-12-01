FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy all necessary modules
COPY api/ /app/api/
COPY helpers/ /app/helpers/
COPY llm_service/ /app/llm_service/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/api/requirements.txt

# Clean up
RUN find /usr/local/lib/python3.11/site-packages -name 'tests' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11/site-packages -name 'docs' -type d -exec rm -rf {} + 2>/dev/null || true

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
