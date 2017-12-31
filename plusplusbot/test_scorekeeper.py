from .scorekeeper import ScoreKeeper

import tempfile
import csv


def test_new_file_load():
    with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard.keys()) == 0

def test_existing_file_load():
    with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
        writer = csv.writer(temp_file, delimiter=',')
        writer.writerow(["U12345", "10"])
        temp_file.flush()

        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard.keys()) == 1
