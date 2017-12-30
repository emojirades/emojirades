from .scorekeeper import ScoreKeeper

import tempfile


def test_new_file_load():
    with tempfile.NamedTemporaryFile() as temp_file:
        keeper = ScoreKeeper(filename=temp_file.name)

        assert len(keeper.scoreboard.keys()) == 0
