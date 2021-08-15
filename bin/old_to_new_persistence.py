#!/usr/bin/env python3

import argparse
import datetime
import json


def process_score(workspace_id, score_filename):
    with open(score_filename, "rt") as score_file:
        scores = json.load(score_file)

    new_scores = []
    new_score_history = []

    for channel_id, channel_scores in scores.items():
        if channel_id.startswith("D") or channel_id == "null":
            # Weird bug, ignoring for now
            continue

        for user_id, user_score in channel_scores["scores"].items():
            new_scores.append({
                "workspace_id": workspace_id,
                "channel_id": channel_id,
                "user_id": user_id,

                "score": user_score,
            })

        for item in channel_scores["history"]:
            timestamp = datetime.datetime.fromtimestamp(item["timestamp"], tz=datetime.timezone.utc)

            if item["operation"].startswith("Manually"):
                operation = "set"
                before = 0
                after = int(item["operation"].split(" ")[3])
            else:
                operation = item["operation"]
                before = 0
                after = 0

            new_score_history.append({
                "workspace_id": workspace_id,
                "channel_id": channel_id,
                "user_id": item["user_id"],

                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "operation": f"{operation},{before},{after}",
            })

    with open(f"{score_filename}.processed_scores", "wt") as new_scores_file:
        json.dump(new_scores, new_scores_file, indent=4, sort_keys=True)

    with open(f"{score_filename}.processed_score_history", "wt") as new_score_history_file:
        json.dump(new_score_history, new_score_history_file, indent=4, sort_keys=True)


def process_state(workspace_id, state_filename):
    with open(state_filename, "rt") as state_file:
        state = json.load(state_file)

    new_state = []

    for channel_id, channel_state in state.items():
        if channel_id.startswith("D") or channel_id == "null":
            # Weird bug, ignoring for now
            continue

        new_state.append({
            "workspace_id": workspace_id,
            "channel_id": channel_id,

            "step": channel_state["step"].upper(),
            "current_winner": channel_state["winner"],
            "previous_winner": channel_state["old_winner"],
            "emojirade": json.dumps(channel_state["emojirade"]) if channel_state["emojirade"] else None,
            "raw_emojirade": json.dumps(channel_state["raw_emojirade"]) if channel_state["raw_emojirade"] else None,
            "first_guess": False,
            "admins": json.dumps(channel_state["admins"]),
        })

    with open(f"{state_filename}.processed", "wt") as new_state_file:
        json.dump(new_state, new_state_file, indent=4, sort_keys=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--score-file")
    parser.add_argument("--state-file")

    args = parser.parse_args()

    if args.score_file:
        process_score(args.workspace_id, args.score_file)

    if args.state_file:
        process_state(args.workspace_id, args.state_file)
