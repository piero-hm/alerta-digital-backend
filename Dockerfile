FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser \
    && chown appuser:appuser /app

COPY --chown=appuser:appuser pyproject.toml uv.lock .python-version ./

USER appuser

RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
