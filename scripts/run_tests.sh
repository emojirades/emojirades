#!/bin/bash

./tests/slack_ws.py &
WS_PID=$!

pytest tests/test_commands.py
pytest tests/test_event.py
pytest tests/test_gamestate.py
pytest tests/test_leaderboard.py
pytest tests/test_scenarios.py
pytest tests/test_scorekeeper.py
pytest tests/test_time_range.py

kill "${WS_PID}"
