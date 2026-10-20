FROM ghcr.io/astral-sh/uv:0.9.4@sha256:c4089b0085cf4d38e38d5cdaa5e57752c1878a6f41f2e3a3a234dc5f23942cb4 AS uv
FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /opt/hermes
COPY vendor/hermes-runtime/ ./
# Use Hermes' package manager and its committed dependency lock.
RUN python -m pm.build_env --source /opt/hermes --python /usr/local/bin/python \
    --out /opt/hermes/.venv --no-install-project --sealed
ENV PATH="/opt/hermes/.venv/bin:$PATH" PYTHONPATH=/opt/hermes \
    HERMES_HOME=/auth PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --uid 1000 --create-home auditor && mkdir /reports /auth && chown auditor:auditor /reports /auth
WORKDIR /app
COPY auditor/ ./
USER auditor
ENTRYPOINT ["python", "/app/audit.py"]
