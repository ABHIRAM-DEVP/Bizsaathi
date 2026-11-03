FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/media \
    && chown -R app:app /app

COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=120 \
    UV_HTTP_RETRIES=3 \
    UV_CONCURRENT_DOWNLOADS=1

RUN uv sync --frozen --no-dev

COPY --chown=app:app alembic ./alembic
COPY --chown=app:app app ./app
COPY --chown=app:app docker-entrypoint.py ./

USER app

EXPOSE 8080

ENTRYPOINT ["python", "docker-entrypoint.py"]
