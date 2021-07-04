from unittest import TestCase
from unittest import mock

from emojirades.scorekeeper import ScoreKeeper
from emojirades.tests.helper import (
    EmojiradeBotTester
)

import tempfile
import json
import time


class ScoreKeeperTester(TestCase):
    def test_new_file_load(self):
        with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
            keeper = ScoreKeeper(score_uri=f"file://{temp_file.name}")

            self.assertEqual(len(keeper.scoreboard.keys()), 0)

    def test_existing_file_load(self):
        self.channel = "C00001"
        user = "U12345"

        scoreboard = {
            self.channel: {
                "scores": {
                    user: 1,
                },
                "history": [
                    {"timestamp": 1593565068.205327, "user_id": user, "operation": "++"}
                ],
            },
        }

        with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
            temp_file.write(json.dumps(scoreboard))
            temp_file.flush()

            keeper = ScoreKeeper(score_uri=f"file://{temp_file.name}")

            self.assertEqual(len(keeper.scoreboard[self.channel]["scores"].keys()), 1)


class ScoreKeeperIntegrationTest(TestCase):
    @mock.patch("time.time", return_value=1593565068.205327)
    def setUp(self, mock_time):
        self.channel = "C00001"
        self.user_1 = "U12345"
        self.user_2 = "U54321"

        scoreboard = {
            self.channel: {
                "scores": {
                    self.user_1: 10,
                },
                "history": [
                    {
                        "timestamp": 1593565068.205327,
                        "user_id": self.user_1,
                        "operation": "++",
                    }
                ],
            },
        }

        self.temp_file = tempfile.NamedTemporaryFile(mode="wt", newline="")
        self.temp_file.write(json.dumps(scoreboard))
        self.temp_file.flush()

        keeper = ScoreKeeper(score_uri=f"file://{self.temp_file.name}")
        keeper.plusplus(self.channel, self.user_1)
        keeper.plusplus(self.channel, self.user_2)
        keeper.minusminus(self.channel, self.user_2)
        keeper.overwrite(self.channel, self.user_1, 300)
        keeper.save()
        del keeper

        self.keeper = ScoreKeeper(score_uri=f"file://{self.temp_file.name}")

    def tearDown(self):
        self.temp_file.close()

    def test_score_keeping(self):
        self.assertEqual(len(self.keeper.scoreboard[self.channel]["scores"].keys()), 2)
        self.assertEqual(
            self.keeper.scoreboard[self.channel]["scores"][self.user_1], 300
        )
        self.assertEqual(self.keeper.scoreboard[self.channel]["scores"][self.user_2], 0)

    def test_history(self):
        self.assertEqual(len(self.keeper.scoreboard[self.channel]["history"]), 5)
        self.assertEqual(
            self.keeper.scoreboard[self.channel]["history"],
            [
                {
                    "operation": "++",
                    "timestamp": 1593565068.205327,
                    "user_id": "U12345",
                },
                {
                    "operation": "++",
                    "timestamp": 1593565068.205327,
                    "user_id": "U12345",
                },
                {
                    "operation": "++",
                    "timestamp": 1593565068.205327,
                    "user_id": "U54321",
                },
                {
                    "operation": "--",
                    "timestamp": 1593565068.205327,
                    "user_id": "U54321",
                },
                {
                    "operation": "Manually set to 300",
                    "timestamp": 1593565068.205327,
                    "user_id": "U12345",
                },
            ],
        )
