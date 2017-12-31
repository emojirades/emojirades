from .scorekeeper import ScoreKeeper

import tempfile
import csv


def test_new_file_load():
    with tempfile.NamedTemporaryFile() as temp_file:
        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard.keys()) == 0

def test_existing_file_load():
    with tempfile.NamedTemporaryFile() as temp_file:
        writer = csv.writer(temp_file, delimiter=',')
        writer.writerow(['U12345', '10'])

        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard.keys()) == 1
