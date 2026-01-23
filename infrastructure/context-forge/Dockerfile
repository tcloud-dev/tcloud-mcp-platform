FROM python:3.12-slim AS builder

# Install dependencies to a directory we can copy
RUN pip install --target=/deps --no-cache-dir \
    python-jose[cryptography]>=3.3.0 \
    pydantic-settings>=2.0.0

FROM ghcr.io/ibm/mcp-context-forge:latest

# Copy installed dependencies
COPY --from=builder /deps /app/.venv/lib/python3.12/site-packages/

# Copy plugin code
COPY plugins/tcloud_cognito_auth /app/plugins/tcloud_cognito_auth
