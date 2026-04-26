#!/bin/bash -e

# Start the mock Slack WebSocket server in the background
uv run --extra dev ./tests/slack_ws.py &
WS_PID=$!

# Ensure the background process is killed on exit, even if tests fail
trap "kill ${WS_PID}" EXIT

# Run tests using the dev environment
uv run --extra dev python -m pytest
