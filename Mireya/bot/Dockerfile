FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY bot/ /app/bot/
COPY helpers/ /app/helpers/
COPY llm_service/ /app/llm_service/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/bot/requirements.txt

RUN find /usr/local/lib/python3.11/site-packages -name 'tests' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11/site-packages -name 'docs' -type d -exec rm -rf {} + 2>/dev/null || true

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "bot.main"]
