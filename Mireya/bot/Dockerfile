FROM python:3.11-slim

WORKDIR /app

COPY bot/ /app/bot

RUN pip install --no-cache-dir --only-binary=:all: numpy pandas matplotlib scikit-learn || \
    pip install --no-cache-dir -r /app/bot/requirements.txt
RUN find /usr/local/lib/python3.11/site-packages -name 'tests' -type d -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -name 'docs' -type d -exec rm -rf {} +


CMD ["python3", "-m", "bot.main"]