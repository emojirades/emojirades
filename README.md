# Emojirades
A Slack bot that understands the Emojirades game and handles scorekeeping.

![CI Status](https://github.com/emojirades/emojirades/actions/workflows/ci.yml/badge.svg)

## Quick Start (Development)

This project uses `uv` for dependency management.

### Setup Environment
```bash
# Create venv and install dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

### Run Tests
```bash
# Run the test suite
uv run ./scripts/run_tests.sh
```

## Running the Bot

### Initialization
```bash
# Initialize the database (SQLite)
uv run emojirades init --db-uri "sqlite:///emojirades.db"
```

### Run (Single Workspace)
```bash
uv run emojirades single --db-uri "sqlite:///emojirades.db" --auth-uri "auth.json"
```

### Run (Docker)
```bash
docker build -t emojirades .
docker run -e DATABASE_URI=sqlite:////data/emojirades.db -v $(pwd)/data:/data emojirades
```

## Database Migrations
We use Alembic for database migrations.
```bash
# Apply migrations
uv run emojirades init

# Generate a new migration (after modifying models)
export PYTHONPATH=src
cd src/emojirades/persistence/models
uv run alembic revision --autogenerate -m "description of changes"
```

## Deployment
The bot is automatically published to GHCR on tagged releases. See `src/emojirades/__init__.py` for the current version.
