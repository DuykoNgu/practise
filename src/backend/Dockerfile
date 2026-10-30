FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/src/backend

COPY src/backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY src/backend/alembic.ini ./
COPY src/backend/alembic ./alembic
COPY src/backend/app ./app
COPY src/database /app/src/database

RUN useradd --system --no-create-home cic \
    && mkdir -p /app/storage/imports \
    && chown -R cic /app/storage
USER cic

ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    FILE_STORAGE_DIR=/app/storage/imports

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "-c", "case \"$1\" in api) exec uvicorn app.main:create_app --factory --host \"$API_HOST\" --port \"$API_PORT\" ;; worker) exec python -m app.worker ;; *) exec \"$@\" ;; esac", "--"]
CMD ["api"]
