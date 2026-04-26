# Emojirades
A Slack bot that understands the Emojirades game and handles scorekeeping.

![CI Status](https://github.com/emojirades/emojirades/actions/workflows/ci.yml/badge.svg)

## Local Development Setup

This project uses `uv` for dependency management. Follow these steps to set up your local environment:

### 1. Install dependencies
Install the project and all development tools into a local virtual environment:
```bash
uv sync --extra dev
```

### 2. Configure Git Hooks
We use `pre-commit` to ensure code quality. Initialize the hooks so they run automatically on `git commit`:
```bash
uv run pre-commit install
```

### 3. Run Tests
Ensure everything is working correctly:
```bash
uv run --extra dev ./scripts/run_tests.sh
```

## Running the Bot Locally

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

## Dependency Management

This project uses `uv` for lightning-fast dependency management and deterministic builds.

### Adding/Updating Dependencies
```bash
# Add a new package
uv add requests

# Add a dev dependency
uv add --dev pytest

# Update a specific package
uv add requests@latest

# Update all packages to latest allowed by constraints
uv lock --upgrade
```

### Syncing Environment
If the `uv.lock` or `pyproject.toml` file changes, sync your local environment:
```bash
uv sync
```

## Database Migrations
We use Alembic for database migrations.
```bash
# Apply migrations
uv run emojirades init

# Generate a new migration (after modifying models)
# This can now be run directly from the root
uv run alembic revision --autogenerate -m "description of changes"
```

## Deployment
The bot is automatically published to GHCR on tagged releases. See `src/emojirades/__init__.py` for the current version.
