FROM python:3.11-slim

WORKDIR /app

COPY api/ /app/api
COPY ./bot/services/ /app/bot/services

RUN pip install --no-cache-dir -r /app/api/requirements.txt

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9000"]
