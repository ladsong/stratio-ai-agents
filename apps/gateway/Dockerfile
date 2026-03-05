FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY packages/core/ /tmp/core/
RUN pip install --no-cache-dir -e /tmp/core

COPY apps/gateway/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/gateway/src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
