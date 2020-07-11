#!/usr/bin/env python3

from datetime import datetime

import pendulum
import json
import csv


tz = pendulum.timezone("Australia/Melbourne")
history_filename = "emojirades/tests/fixtures/history.json"

with open(history_filename) as history_file:
    history = json.load(history_file)

with open("history.csv", "w") as csv_file:
    fieldnames = history[0].keys()

    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for event in history:
        event["timestamp"] = datetime.fromtimestamp(event["timestamp"], tz=tz)
        writer.writerow(event)
