FROM ghcr.io/astral-sh/uv:0.9.4@sha256:c4089b0085cf4d38e38d5cdaa5e57752c1878a6f41f2e3a3a234dc5f23942cb4 AS uv
FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704
COPY --from=uv /uv /usr/local/bin/uv
# Git is used only to apply our frontend patch, never to run target hooks/scripts.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY preparation/ ./
COPY docker/hermes3d-local-demo.patch /app/docker/hermes3d-local-demo.patch
RUN python runner.py install-source
WORKDIR /opt/graphify
RUN uv sync --frozen --no-dev --no-editable
RUN uv pip install --python .venv/bin/python --no-deps --require-hashes -r /app/requirements-overlay.lock \
    && uv pip check --python .venv/bin/python
RUN mkdir -p /usr/local/share/licenses/graphify \
    && cp LICENSE LICENSE-MIT NOTICE /usr/local/share/licenses/graphify/ \
    && useradd --uid 1000 --create-home preparer
ENV PATH="/opt/graphify/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    GRAPHIFY_BACKEND=none GRAPHIFY_QUERY_LOG_DISABLE=1 PYTHONHASHSEED=0 \
    PYTHONSAFEPATH=1 PYTHONPATH=/app HOME=/tmp/home
WORKDIR /app
USER preparer
ENTRYPOINT ["python", "/app/runner.py"]
