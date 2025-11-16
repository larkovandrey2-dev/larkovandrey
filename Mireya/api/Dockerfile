FROM python:3.11-slim

WORKDIR /app

COPY api/ /app/api
COPY ./bot/services/ /app/bot/services

RUN pip install --no-cache-dir --only-binary=:all:matplotlib|| \
    pip install --no-cache-dir -r /app/api/requirements.txt
RUN find /usr/local/lib/python3.11/site-packages -name 'tests' -type d -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -name 'docs' -type d -exec rm -rf {} +

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]