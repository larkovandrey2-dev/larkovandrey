FROM python:3.11-slim

WORKDIR /app

COPY bot/ /app/bot
COPY api/ /app/api

RUN pip install --no-cache-dir -r requirements.txt
COPY .env .env
ENV $(cat .env | xargs)
CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]