import pytest
import json

from emojirades.slack.event import Event
from emojirades.tests.FileFixture import FileFixture


class TestEvent:
    @pytest.fixture
    def bot_event(self):
        with FileFixture("bot_event.json").open() as ff:
            return Event(json.load(ff))

    @pytest.fixture
    def user_event(self):
        with FileFixture("user_event.json").open() as ff:
            return Event(json.load(ff))

    def test_get_user_player_id(self, user_event):
        assert user_event.player_id() == "USERID002"

    def test_get_bot_player_id(self, bot_event):
        assert  bot_event.player_id() == "BOTID0001"
