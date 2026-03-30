FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Install packages in dependency order: core first, then server.
# Copies only what's needed — no tests, dev tooling, or workspace root.
COPY packages/core/ packages/core/
COPY packages/server/ packages/server/

RUN pip install --no-cache-dir packages/core/ && \
    pip install --no-cache-dir packages/server/

# ── Runtime image ──────────────────────────────────────────────────────────────

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/kodiak-server /usr/local/bin/kodiak-server

# Runtime directories for Kodiak data and config
RUN mkdir -p /app/config /app/data /app/logs

EXPOSE 6704

CMD ["kodiak-server", "--host", "0.0.0.0", "--port", "6704"]
