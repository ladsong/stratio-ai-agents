FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir nanobot-ai httpx loguru sqlalchemy psycopg[binary] cryptography pgvector

COPY packages/core/src/core /app/core

COPY apps/nanobot-gateway/src/ ./

ENV PYTHONPATH=/app

CMD ["python", "-m", "nanobot_gateway.main"]
