#!/usr/bin/env python3

import json
import csv
import pendulum
from datetime import datetime

history_file = 'plusplusbot/tests/fixtures/history.json'

history = json.load(open(history_file))

with open('history.csv', 'w') as csv_file:

    fieldnames = history[0].keys()
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for event in history:
        event['timestamp'] = datetime.fromtimestamp(event['timestamp'], tz=pendulum.timezone('Australia/Melbourne'))
        writer.writerow(event)


