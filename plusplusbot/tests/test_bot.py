from plusplusbot.bot import PlusPlusBot
from unittest.mock import patch

import unittest
import tempfile
import logging
import csv
import os

logging.basicConfig(level=logging.DEBUG)

class TestPlusPlusBot(unittest.TestCase):
    slack_token = "xoxb-000000000000-aaaaaaaaaaaaaaaaaaaaaaaa"

    team = "T00000001"
    channel = "C00000001"
    bot_id = "U00000000"
    bot_channel = "D00000001"
    player_1 = "U00000001"
    player_2 = "U00000002"
    player_3 = "U00000003"

    def save_responses(self, channel, message):
        self.responses.append((channel, message))

    @patch("plusplusbot.bot.SlackClient")
    def setUp(self, slack_client):
        self.scorefile = tempfile.NamedTemporaryFile()
        self.statefile = tempfile.NamedTemporaryFile()

        os.environ["SLACK_BOT_TOKEN"] = self.slack_token

        self.bot = PlusPlusBot(self.scorefile.name, self.statefile.name)
        self.bot.slack.bot_id = self.bot_id
        self.bot.slack.sc.rtm_send_message = self.save_responses

        self.responses = []

    def tearDown(self):
        self.scorefile.close()
        self.statefile.close()

    @patch("time.sleep", side_effect=InterruptedError)
    def feed(self, events, sleep):
        self.bot.slack.sc.rtm_read.return_value = events

        try:
            self.bot.listen_for_actions()
        except InterruptedError:
            pass

    def test_valid_transitions(self):
        """ Feeds state transition events to the bot in the correct order """
        assert self.bot.gamestate.state[self.channel]["step"] == "new_game"

        start_game_event = {
            "team": self.team,
            "source_team": self.team,
            "channel": self.channel,
            "user": self.player_1,
            "type": "message",
            "text": "<@{0}> new game <@{1}> <@{2}>".format(self.bot_id, self.player_1, self.player_2),
            "ts": "1000000000.000001",
        }

        self.feed([start_game_event])

        assert self.bot.gamestate.state[self.channel]["step"] == "waiting"

        posted_emojirade_event = {
            "team": self.team,
            "source_team": self.team,
            "channel": self.bot_channel,
            "user": self.player_1,
            "type": "message",
            "text": "emojirade testing".format(self.bot_id, self.player_1, self.player_2),
            "ts": "1000000000.000001",
        }

        self.feed([posted_emojirade_event])

        assert self.bot.gamestate.state[self.channel]["step"] == "provided"

        posted_emoji_event = {
            "team": self.team,
            "source_team": self.team,
            "channel": self.channel,
            "user": self.player_2,
            "type": "message",
            "text": ":waddle:",
            "ts": "1000000000.000001",
        }

        self.feed([posted_emoji_event])

        assert self.bot.gamestate.state[self.channel]["step"] == "guessing"

        correct_guess_event = {
            "team": self.team,
            "source_team": self.team,
            "channel": self.channel,
            "user": self.player_3,
            "type": "message",
            "text": "testing",
            "ts": "1000000000.000001",
        }

        self.feed([correct_guess_event])

        assert self.bot.gamestate.state[self.channel]["step"] == "waiting"

    def test_plusplus_new_game(self):
        """ Cannot ++ someone when the game is not in progress """
        assert self.bot.gamestate.state[self.channel]["step"] == "new_game"

        plusplus_event = {
            "team": self.team,
            "source_team": self.team,
            "channel": self.channel,
            "user": self.player_1,
            "type": "message",
            "text": "<@{0}>++".format(self.player_2),
            "ts": "1000000000.000001",
        }

        self.feed([plusplus_event])

        assert (self.channel, "Sorry but we need to be actively guessing! Get the winner to start posting the next 'rade!") in self.responses
