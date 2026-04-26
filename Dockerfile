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

# Install the wheel using pip. We use --no-cache-dir to keep the image small.
# The dependencies are automatically resolved and installed from the wheel.
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Set the entrypoint to the console script defined in pyproject.toml
ENTRYPOINT ["emojirades"]
