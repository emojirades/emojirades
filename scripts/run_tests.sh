#!/bin/bash -e

# Start the mock Slack WebSocket server in the background
# Ensure src is in PYTHONPATH so it can find emojirades if needed (though slack_ws.py seems standalone)
export PYTHONPATH=src
uv run --extra dev ./tests/slack_ws.py &
WS_PID=$!

# Give the server a bit more time to start
sleep 2

# Ensure the background process is killed on exit, even if tests fail
trap "kill ${WS_PID} 2>/dev/null || true" EXIT

# Run tests using the dev environment
# PYTHONPATH is already exported above
uv run --extra dev python -m pytest
