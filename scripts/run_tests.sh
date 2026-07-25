#!/bin/bash -e

# Ensure src is in PYTHONPATH
export PYTHONPATH=src

# Run tests using pytest (mock WebSocket server is managed via conftest.py session fixture)
uv run --extra dev python -m pytest "$@"
