# Production Dockerfile for Backend using uv
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml .

# Install dependencies using uv sync
RUN uv venv /app/.venv && uv pip install -r <(uv pip compile pyproject.toml)

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy virtualenv and app
COPY --from=builder /app/.venv /app/.venv
COPY app /app/app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "app.main"]
