# Dockerfile for the trading system
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY .. .
CMD ["python", "src/main.py"]
