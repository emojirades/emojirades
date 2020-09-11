from emojirades.bot import EmojiradesBot
from unittest.mock import patch, Mock

import unittest
import tempfile
import logging
import os

# export LOGGING_LEVEL=10 to turn on debug
logging.basicConfig(level=int(os.getenv("LOGGING_LEVEL", logging.ERROR)))


class EmojiradeBotTester(unittest.TestCase):
    """
    Base testing class that creates a bot that will accept events to test against
    """

    def send_event(self, event):
        web_client = Mock()
        web_client.chat_postMessage = self.save_responses
        web_client.reactions_add = self.save_reactions

        payload = {
            "data": event,
            "web_client": web_client,
        }

        self.bot.handle_event(**payload)

    def reset_and_transition_to(self, state):
        """ From the beginning state, transition to another state the user wants """
        self.setUp()
        assert self.state["step"] == "new_game"

        if state == "waiting":
            events = [self.events.new_game]
        elif state == "provided":
            events = [self.events.new_game, self.events.posted_emojirade]
        elif state == "guessing":
            events = [
                self.events.new_game,
                self.events.posted_emojirade,
                self.events.posted_emoji,
            ]
        elif state == "guessed":
            events = [
                self.events.new_game,
                self.events.posted_emojirade,
                self.events.posted_emoji,
                self.events.correct_guess,
            ]
        else:
            raise RuntimeError(
                f"Invalid state ({state}) provided to TestEmojiradesBot.transition_to()"
            )

        for event in events:
            self.send_event(event)

    def save_responses(self, channel=None, text=None):
        self.responses.append((channel, text))

    def save_reactions(self, channel=None, name=None, timestamp=None):
        self.reactions.append((channel, name, timestamp))

    def find_im(self, user_id):
        return user_id.replace("U", "D")

    def pretty_name(self, user_id):
        return user_id

    @patch("slack.RTMClient", autospec=True)
    @patch("slack.WebClient", autospec=True)
    def setUp(self, web_client, rtm_client):
        self.responses = []
        self.reactions = []

        self.config, self.events = self.prepare_event_data()

        self.scorefile = tempfile.NamedTemporaryFile()
        self.statefile = tempfile.NamedTemporaryFile()

        os.environ["SLACK_BOT_TOKEN"] = "xoxb-000000000000-aaaaaaaaaaaaaaaaaaaaaaaa"

        self.bot = EmojiradesBot(self.scorefile.name, self.statefile.name)
        self.bot.slack.bot_id = self.config.bot_id
        self.bot.slack.find_im = self.find_im
        self.bot.slack.pretty_name = self.pretty_name

        self.state = self.bot.gamestate.state[self.config.channel]
        self.scoreboard = self.bot.scorekeeper.scoreboard[self.config.channel]

    def tearDown(self):
        self.scorefile.close()
        self.statefile.close()

    @staticmethod
    def prepare_event_data():
        team = "T00000001"
        channel = "C00000001"
        bot_id = "U00000000"
        bot_channel = "D00000000"
        player_1 = "U00000001"
        player_1_channel = "D00000001"
        player_2 = "U00000002"
        player_2_channel = "D00000002"
        player_3 = "U00000003"
        player_3_channel = "D00000003"
        player_4 = "U00000004"
        player_4_channel = "D00000004"
        emojirade = "testing"

        event_config = {
            "team": team,
            "channel": channel,
            "bot_id": bot_id,
            "bot_channel": bot_channel,
            "player_1": player_1,
            "player_1_channel": player_1_channel,
            "player_2": player_2,
            "player_2_channel": player_2_channel,
            "player_3": player_3,
            "player_3_channel": player_3_channel,
            "player_4": player_4,
            "player_4_channel": player_4_channel,
            "emojirade": emojirade,
        }

        base_event = {
            "team": team,
            "source_team": team,
            "channel": channel,
            "type": "message",
            "ts": "1000000000.000001",
        }

        event_registry = {
            "base": base_event,
            "new_game": {
                **base_event,
                **{
                    "user": player_1,
                    "text": f"<@{bot_id}> new game <@{player_1}> <@{player_2}>",
                    "ts": "1000000000.000002",
                },
            },
            "posted_emojirade": {
                **base_event,
                **{
                    "channel": bot_channel,
                    "user": player_1,
                    "text": f"emojirade {emojirade}",
                    "ts": "1000000000.000003",
                },
            },
            "posted_emoji": {
                **base_event,
                **{"user": player_2, "text": ":waddle:", "ts": "1000000000.000004", },
            },
            "incorrect_guess": {
                **base_event,
                **{"user": player_3, "text": "foobar", "ts": "1000000000.000005", },
            },
            "correct_guess": {
                **base_event,
                **{"user": player_3, "text": emojirade, "ts": "1000000000.000006", },
            },
            "manual_award": {
                **base_event,
                **{
                    "user": player_2,
                    "text": f"<@{player_3}>++",
                    "ts": "1000000000.000007",
                },
            },
            "plusplus": {
                **base_event,
                **{
                    "user": player_1,
                    "text": f"<@{player_2}>++",
                    "ts": "1000000000.000008",
                },
            },
            "leaderboard": {
                **base_event,
                **{
                    "user": player_1,
                    "text": f"<@{bot_id}> leaderboard all time",
                    "ts": "1000000000.000009",
                },
            },
            "game_status": {
                **base_event,
                **{
                    "user": player_1,
                    "text": f"<@{bot_id}> game status",
                    "ts": "1000000000.000010",
                },
            },
            "help": {
                **base_event,
                **{
                    "user": player_1,
                    "text": f"<@{bot_id}> help",
                    "ts": "1000000000.000011",
                },
            },
            "fixwinner": {
                **base_event,
                **{
                    "user": player_2,
                    "text": f"<@{bot_id}> fixwinner <@{player_4}>",
                    "ts": "1000000000.000012",
                },
            },
        }

        class Foo(object):
            pass

        events = Foo()
        config = Foo()

        for k, v in event_registry.items():
            setattr(events, k, v)

        for k, v in event_config.items():
            setattr(config, k, v)

        return config, events
