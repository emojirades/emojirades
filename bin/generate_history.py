#!/usr/bin/env python3

from datetime import datetime, timedelta
import random
import json

start_date = datetime(2020, 4, 15)
end_date = datetime(2020, 6, 20)

users = ["U985L6R1M", "U0ZC11HC7", "U5HKU1Q0W", "U0VCW825A"]

ops_probs = (["++"] * 99) + ["--"]

delta = end_date - start_date

history = []

for i in range(delta.days + 1):
    day = start_date + timedelta(days=i)

    n_events = random.randint(5, 10)

    for t in range(n_events):
        event_ts = day + timedelta(hours=9 + t)
        user = random.choice(users)
        ops = random.choice(ops_probs)

        history.append(
            {"operation": ops, "timestamp": event_ts.timestamp(), "user_id": user}
        )

json.dump(history, open("history.json", "w"))
