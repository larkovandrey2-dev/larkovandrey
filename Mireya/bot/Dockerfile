FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

COPY bot/ /app/bot

RUN pip install --no-cache-dir -r /app/bot/requirements.txt
CMD ["python3", "-m", "bot.main"]