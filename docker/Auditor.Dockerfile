FROM ghcr.io/astral-sh/uv:0.9.4@sha256:c4089b0085cf4d38e38d5cdaa5e57752c1878a6f41f2e3a3a234dc5f23942cb4 AS uv
FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS package-build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /build
COPY pyproject.toml ./
COPY backend/src/ ./backend/src/
COPY docs/ESTANDAR_COMUNICACION_INFORMES.md ./docs/ESTANDAR_COMUNICACION_INFORMES.md
RUN uv build --wheel --out-dir /wheels .

FROM python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS backend-base
COPY --from=uv /uv /usr/local/bin/uv
COPY docker/install_scanners.py /tmp/install_scanners.py
RUN python /tmp/install_scanners.py && rm /tmp/install_scanners.py
WORKDIR /opt/hermes
COPY vendor/hermes-runtime/ ./
# Use Hermes' package manager and its committed dependency lock.
RUN python -m pm.build_env --source /opt/hermes --python /usr/local/bin/python \
    --out /opt/hermes/.venv --no-install-project --sealed
ENV PATH="/opt/hermes/.venv/bin:$PATH" PYTHONPATH=/opt/hermes \
    HERMES_HOME=/auth PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --uid 1000 --create-home auditor && mkdir /reports /auth && chown auditor:auditor /reports /auth
WORKDIR /app
COPY --from=package-build /wheels/ /tmp/arktic-wheels/
RUN uv pip install --python /opt/hermes/.venv/bin/python --no-deps /tmp/arktic-wheels/*.whl \
    && rm -r /tmp/arktic-wheels
ARG APP_VERSION=0.0.0-dev
ENV ARKTIC_BACKEND_VERSION=$APP_VERSION
LABEL org.opencontainers.image.title="Arktic Office Backend" org.opencontainers.image.version=$APP_VERSION
COPY auditor/ ./
COPY licenses/ /usr/local/share/licenses/arktic/
USER auditor
ENTRYPOINT ["python", "/app/audit.py"]

FROM backend-base AS tests
COPY backend/tests/ /tests/
WORKDIR /tests
ENTRYPOINT ["python", "/tests/run_offline.py"]

# The default image contains the installed package/resources and launchers only.
FROM backend-base AS runtime
