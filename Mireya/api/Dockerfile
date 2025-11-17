FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && find /usr/local/lib/python3.11/site-packages -name 'tests' -type d -exec rm -rf {} + \
    && find /usr/local/lib/python3.11/site-packages -name 'docs' -type d -exec rm -rf {} +

COPY main.py /app/api/
COPY ./services /app/services
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
