# Stage 1: Build the wheel using uv
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

# Enable bytecode compilation for faster startup in the final image
ENV UV_COMPILE_BYTECODE=1

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . .

# Build the project wheel using uv
RUN uv build --wheel --out-dir /dist


# Stage 2: Final production image
FROM python:3.14-slim-trixie

# Set environment variables for better logging and container behavior
ENV PYTHONUNBUFFERED=1

# Copy the built wheel from the builder stage
COPY --from=builder /dist/*.whl /tmp/

# Copy Alembic migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/migrations /app/migrations

# Install the wheel using pip
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Set the working directory to where alembic.ini is
WORKDIR /app

# Set the entrypoint
ENTRYPOINT ["emojirades"]
