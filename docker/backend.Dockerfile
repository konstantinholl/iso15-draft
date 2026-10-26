FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/backend

RUN pip install --no-cache-dir uv
COPY backend/pyproject.toml backend/README.md ./
RUN uv pip install --system -e .[dev]

COPY backend/ ./

EXPOSE 8000
