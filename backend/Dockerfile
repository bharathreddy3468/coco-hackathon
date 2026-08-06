FROM python:3.11-slim as builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml .

RUN uv venv /app/.venv
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY app /app/app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]