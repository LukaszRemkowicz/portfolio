FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    TZ=Europe/Warsaw \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app/collector

COPY collector/pyproject.toml pyproject.toml
COPY collector/README.md README.md
COPY collector/uv.lock uv.lock
COPY collector/src src
RUN uv sync --frozen --no-dev --no-editable

CMD ["portfolio-log-collector"]
