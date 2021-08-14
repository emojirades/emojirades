from unittest import TestCase
from unittest import mock

from emojirades.gamestate import Gamestate
from emojirades.tests.helper import (
    EmojiradeBotTester
)

import tempfile
import json
import time


class GamestateTester(TestCase):
    def setUp(self):
        self.gamestate = Gamestate(db_uri="sqlite+pysqlite:///:memory:", workspace_id="T12345678")

    def test_new_file_load(self):
        self.assertEqual(len(gamestate.state.keys()), 0)

    def test_existing_file_load(self):
        self.channel = "C00001"
        user = "U12345"

        state = {
            self.channel: {
                "step": "new_game",
                "old_winner": None,
                "winner": user,
                "emojirade": None,
                "raw_emojirade": None,
                "admins": [],
            },
        }

        with tempfile.NamedTemporaryFile(mode="wt", newline="") as temp_file:
            temp_file.write(json.dumps(state))
            temp_file.flush()

            gamestate = Gamestate(state_uri=f"file://{temp_file.name}")

            self.assertEqual(gamestate.state[self.channel]["winner"], user)


class GamestateIntegrationTest(TestCase):
    def setUp(self):
        self.channel = "C00001"
        self.user_1 = "U12345"
        self.user_2 = "U54321"
        self.emojirade = "example"

        state = {
            self.channel: {
                "step": "guessing",
                "old_winner": self.user_1,
                "winner": self.user_2,
                "emojirade": self.emojirade,
                "raw_emojirade": self.emojirade,
                "admins": [],
            },
        }

        self.temp_file = tempfile.NamedTemporaryFile(mode="wt", newline="")
        self.temp_file.write(json.dumps(state))
        self.temp_file.flush()

        gamestate = Gamestate(state_uri=f"file://{self.temp_file.name}")
        gamestate.set_admin(self.channel, self.user_1)
        gamestate.new_game(self.channel, self.user_1, self.user_2)
        gamestate.set_emojirade(self.channel, self.emojirade, self.user_1)
        gamestate.winner_posted(self.channel, self.user_1)
        gamestate.save()
        del gamestate

        self.gamestate = Gamestate(state_uri=f"file://{self.temp_file.name}")

    def tearDown(self):
        self.temp_file.close()

    def test_game_state(self):
        self.assertEqual(self.gamestate.state[self.channel]["winner"], self.user_2)
        self.assertEqual(self.gamestate.game_status(self.channel)["step"], "guessing")
        self.assertEqual(self.gamestate.is_admin(self.channel, self.user_1), True)
