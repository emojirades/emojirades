from plusplusbot.scorekeeper import ScoreKeeper

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


def test_file_format():
    temp_file = tempfile.NamedTemporaryFile(mode="wt", newline="")
    writer = csv.writer(temp_file, delimiter=',')
    writer.writerow(["U12345", "10"])
    temp_file.flush()

    keeper = ScoreKeeper(filename=temp_file.name)
    keeper.plusplus("U12345")
    keeper.plusplus("U54321")
    keeper.save()
    del(keeper)

    keeper = ScoreKeeper(filename=temp_file.name)
    assert len(keeper.scoreboard.keys()) == 2
    assert keeper.scoreboard["U12345"] == 11
    assert keeper.scoreboard["U54321"] == 1
