from plusplusbot.scorekeeper import ScoreKeeper

import tempfile
import json
import csv


def test_new_file_load():
    with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard.keys()) == 0


def test_existing_file_load():
    channel = "C00001"
    user = "U12345"

    scoreboard = {
        channel: {
            "scores": {
                user: 1,
            },
            "history": [(user, "++")],
        },
    }

    with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
        temp_file.write(json.dumps(scoreboard))
        temp_file.flush()

        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard[channel]["scores"].keys()) == 1


def test_file_format():
    channel = "C00001"
    user_1 = "U12345"
    user_2 = "U54321"

    scoreboard = {
        channel:  {
            "scores": {
                user_1: 10,
            },
            "history": [(user_1, "++")],
        },
    }

    with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
        temp_file.write(json.dumps(scoreboard))
        temp_file.flush()

        keeper = ScoreKeeper(filename=temp_file.name)
        keeper.plusplus(channel, user_1)
        keeper.plusplus(channel, user_2)
        keeper.save()
        del(keeper)

        keeper = ScoreKeeper(filename=temp_file.name)
        assert len(keeper.scoreboard[channel]["scores"].keys()) == 2
        assert keeper.scoreboard[channel]["scores"][user_1] == 11
        assert keeper.scoreboard[channel]["scores"][user_2] == 1
