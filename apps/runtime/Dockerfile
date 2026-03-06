FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY packages/core/ /tmp/core/
RUN pip install --no-cache-dir -e /tmp/core

COPY nanobot/ /nanobot/
RUN pip install --no-cache-dir -e /nanobot

COPY apps/runtime/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/runtime/src/ ./src/

RUN mkdir -p /workspace /nanobot/nanobot/skills

EXPOSE 8010

CMD ["uvicorn", "runtime.main:app", "--host", "0.0.0.0", "--port", "8010"]
