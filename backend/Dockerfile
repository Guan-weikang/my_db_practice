FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements/base.txt /app/backend/requirements/base.txt
RUN pip install -r /app/backend/requirements/base.txt

COPY backend /app/backend
COPY deploy/scripts /app/deploy/scripts

RUN chmod +x /app/deploy/scripts/*.sh

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
