FROM python:3.11-slim

WORKDIR /app

COPY bot/ /app/bot

RUN pip install --no-cache-dir -r /app/bot/requirements.txt
CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]