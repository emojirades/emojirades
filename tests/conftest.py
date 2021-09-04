import pytest
import types
import json
import time

from emojirades.persistence import GamestateStep, get_session_factory
from emojirades.scorekeeper import Scorekeeper
from emojirades.gamestate import Gamestate
from emojirades.bot import EmojiradesBot

from tests.slack import (
    setup_mock_web_api_server,
    cleanup_mock_web_api_server,
)


class TestBot:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.slack = self.bot.workspaces[self.config.team]

    @property
    def step(self):
        return self.gamestate.step(self.config.channel)

    def get_xyz(self, xyz):
        return self.gamestate.handler.get_xyz(self.config.channel, xyz)

    def send(self, event):
        self.slack.rtm.send(event)
        time.sleep(0.2)

    def debug(self):
        print("-" * 20)
        print("DEBUG")
        print("-" * 20)
        print(f"Previous Winner: {self.gamestate.winners(self.config.channel)[0]}")
        print(f"Current Winner: {self.gamestate.winners(self.config.channel)[1]}")

        print(
            f"Player 1: {self.scorekeeper.user_score(self.config.channel, self.config.player_1)}"
        )
        print(
            f"Player 2: {self.scorekeeper.user_score(self.config.channel, self.config.player_2)}"
        )
        print(
            f"Player 3: {self.scorekeeper.user_score(self.config.channel, self.config.player_3)}"
        )
        print(
            f"Player 4: {self.scorekeeper.user_score(self.config.channel, self.config.player_4)}"
        )
        print("-" * 20)

    def reset_and_transition_to(self, state, delete=True):
        if delete:
            self.gamestate.handler.delete(iknowwhatimdoing=True)
            self.scorekeeper.handler.delete(iknowwhatimdoing=True)
            time.sleep(0.2)

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
            print(f"Replaying: {event}")
            self.slack.rtm.send(event)

            # Let the threads catch up
            time.sleep(0.2)


@pytest.fixture
def slack_web_api(request, test_data):
    config, _ = test_data

    class Foo:
        def __init__(self, conf):
            self.config = conf
            self.responses = []
            self.reactions = []

    foo = Foo(config)
    setup_mock_web_api_server(foo)

    yield foo

    cleanup_mock_web_api_server(foo)


@pytest.fixture
def bot(auth_uri, db_uri, test_data):
    config, events = test_data

    bot = EmojiradesBot()
    bot.configure_workspace(
        db_uri,
        auth_uri,
        extra_slack_kwargs={
            "base_url": "http://localhost:8888",
            "auto_reconnect_enabled": False,
            "trace_enabled": False,
        },
    )

    bot.listen_for_commands(blocking=False)

    session_factory = get_session_factory(db_uri)
    session = session_factory()

    test_bot = TestBot(
        bot=bot,
        gamestate=Gamestate(session, config.team),
        scorekeeper=Scorekeeper(session, config.team),
        config=config,
        events=events,
        db_uri=db_uri,
        auth_uri=auth_uri,
    )

    yield test_bot

    test_bot.slack.rtm.close()
    session.close()


@pytest.fixture(scope="session")
def bot_token():
    return {"bot_access_token": "xoxb-000000000000-aaaaaaaaaaaaaaaaaaaaaaaa"}


@pytest.fixture
def auth_uri(tmp_path, bot_token):
    uri = tmp_path / "auth.json"

    with open(uri, "wt", encoding="utf-8") as auth_file:
        json.dump(bot_token, auth_file)

    return str(uri)


@pytest.fixture
def db_uri(tmp_path):
    db_file = tmp_path / "emojirades.db"

    db_uri = f"sqlite:///{db_file}"

    EmojiradesBot.init_db(db_uri)

    return db_uri


@pytest.fixture
def test_data():
    team = "T00000001"
    team_url = f"{team}.slack.com"
    channel = "C00000001"
    bot_id = "U00000000"
    bot_name = "emojirades"
    bot_channel = "D00000000"
    player_1 = "U00000001"
    player_1_name = "Player 1"
    player_1_channel = "D00000001"
    player_2 = "U00000002"
    player_2_name = "Player 2"
    player_2_channel = "D00000002"
    player_3 = "U00000003"
    player_3_name = "Player 3"
    player_3_channel = "D00000003"
    player_4 = "U00000004"
    player_4_name = "Player 4"
    player_4_channel = "D00000004"
    emojirade = "testing"

    event_config = {
        "team": team,
        "team_url": team_url,
        "team_name": team,
        "channel": channel,
        "bot_id": bot_id,
        "bot_name": bot_name,
        "bot_channel": bot_channel,
        "player_1": player_1,
        "player_1_name": player_1_name,
        "player_1_channel": player_1_channel,
        "player_2": player_2,
        "player_2_name": player_2_name,
        "player_2_channel": player_2_channel,
        "player_3": player_3,
        "player_3_name": player_3_name,
        "player_3_channel": player_3_channel,
        "player_4": player_4,
        "player_4_name": player_4_name,
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
            **{
                "user": player_2,
                "text": ":waddle:",
                "ts": "1000000000.000004",
            },
        },
        "incorrect_guess": {
            **base_event,
            **{
                "user": player_3,
                "text": "foobar",
                "ts": "1000000000.000005",
            },
        },
        "correct_guess": {
            **base_event,
            **{
                "user": player_3,
                "text": emojirade,
                "ts": "1000000000.000006",
            },
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

    class Foo:
        pass

    events = Foo()
    config = Foo()

    for k, v in event_registry.items():
        setattr(events, k, v)

    for k, v in event_config.items():
        setattr(config, k, v)

    return config, events
