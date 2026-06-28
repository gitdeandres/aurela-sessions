FROM python:3.12-slim

# Install uv from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# uv and Python runtime configuration
ENV UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  # Make the virtualenv binaries available without explicit activation
  PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copy dependency files first to leverage Docker layer caching.
# Changes to source code won't invalidate this layer unless dependencies change.
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself.
# --frozen ensures the lockfile is respected exactly, no re-resolution.
RUN uv sync --frozen --no-install-project

# Copy the rest of the source code
COPY . .

# Install the project into the existing virtualenv
RUN uv sync --frozen
