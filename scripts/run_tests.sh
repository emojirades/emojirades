#!/bin/bash -e

./tests/slack_ws.py &
WS_PID=$!

pytest

kill "${WS_PID}"
