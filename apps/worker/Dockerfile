FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY packages/core/ /tmp/core/
RUN pip install --no-cache-dir -e /tmp/core

COPY apps/worker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/worker/src/ ./src/

CMD ["python", "-m", "worker.main"]
